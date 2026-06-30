import io
import zipfile
import pytest
from src.grep.office_parser import OfficeParser

def create_mock_xlsx():
    """メモリ上に Excel の最小構成 (XML) を含む ZIP 構造を作成する。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zp:
        # 1. 共有文字列
        shared_strings = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="2" uniqueCount="2">'
            '<si><t>Hello shared</t></si>'
            '<si><t>Another string</t></si>'
            '</sst>'
        )
        zp.writestr('xl/sharedStrings.xml', shared_strings)

        # 2. ワークブック (シート名とIDの紐付け)
        workbook = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="TestSheet1" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'
        )
        zp.writestr('xl/workbook.xml', workbook)

        # 3. リレーション (rId1 -> worksheets/sheet1.xml)
        rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/>'
            '</Relationships>'
        )
        zp.writestr('xl/_rels/workbook.xml.rels', rels)

        # 4. ワークシート (セルの配置)
        # t="s" (shared), v=0 -> "Hello shared", v=1 -> "Another string"
        # 属性なし (numerical), v=123
        sheet = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData>'
            '<row r="1">'
            '<c r="A1" t="s"><v>0</v></c>'
            '<c r="B1" t="s"><v>1</v></c>'
            '</row>'
            '<row r="2">'
            '<c r="C2"><v>999</v></c>'
            '</row>'
            '</sheetData>'
            '</worksheet>'
        )
        zp.writestr('xl/worksheets/sheet1.xml', sheet)

    buf.seek(0)
    return buf

class TestOfficeParser:
    def test_xlsx_parsing_logic(self, tmp_path):
        """Excel のシート名、セル番地、共有文字列および数値データが正しく取得できるか。"""
        xlsx_path = tmp_path / "test.xlsx"
        xlsx_path.write_bytes(create_mock_xlsx().read())

        results = OfficeParser.get_xlsx_content(str(xlsx_path))

        # 期待されるヒット数: A1, B1, C2 (計3件)
        assert len(results) == 3

        # A1: 共有文字列 "Hello shared"
        assert results[0]['text'] == "Hello shared"
        assert results[0]['location'] == "TestSheet1!A1"
        assert results[0]['metadata']['cell'] == "A1"

        # B1: 共有文字列 "Another string"
        assert results[1]['text'] == "Another string"
        assert results[1]['location'] == "TestSheet1!B1"

        # C2: 数値 "999"
        assert results[2]['text'] == "999"
        assert results[2]['location'] == "TestSheet1!C2"

    def test_docx_parsing_logic(self, tmp_path):
        """Word の本文、ヘッダー、フッターの抽出ロジックの検証。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zp:
            # 本文
            doc_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Main Content</w:t></w:r></w:p></w:body>'
                '</w:document>'
            )
            # ヘッダー
            hdr_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:p><w:t>Header Content</w:t></w:p>'
                '</w:hdr>'
            )
            zp.writestr('word/document.xml', doc_xml)
            zp.writestr('word/header1.xml', hdr_xml)

        buf.seek(0)
        docx_path = tmp_path / "test.docx"
        docx_path.write_bytes(buf.read())

        results = OfficeParser.get_docx_content(str(docx_path))

        # 本文とヘッダーの両方が取れているか
        contents = [r['text'] for r in results]
        assert "Main Content" in contents
        assert "Header Content" in contents

        # ロケーションラベルの確認
        labels = [r['location'] for r in results]
        assert "Body P.1" in labels
        assert "Header P.1" in labels

    def test_parser_on_error_handling(self, tmp_path):
        """OfficeParserに壊れたファイルを渡した時に on_error が正しく機能するか。"""
        bad_file = tmp_path / "broken.xlsx"
        bad_file.write_text("invalid content", encoding="utf-8")
        
        errors = []
        def on_error(msg, exc):
            errors.append((msg, exc))
            
        # 1. get_xlsx_content でのエラー検証
        res_xlsx = OfficeParser.get_xlsx_content(str(bad_file), on_error=on_error)
        assert len(res_xlsx) == 0
        assert len(errors) == 1
        assert "Error parsing XLSX" in errors[0][0]
        
        # 2. get_docx_content でのエラー検証
        errors.clear()
        res_docx = OfficeParser.get_docx_content(str(bad_file), on_error=on_error)
        assert len(res_docx) == 0
        assert len(errors) == 1
        assert "Error parsing DOCX" in errors[0][0]

    def test_xlsx_target_sheets_filtering(self, tmp_path):
        """Excelの特定シート限定のフィルタ機能が動作するか。"""
        # テスト用の複数シートExcelモックを作成
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zp:
            zp.writestr('xl/sharedStrings.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="2">'
                '<si><t>S1 Val</t></si><si><t>S2 Val</t></si>'
                '</sst>'
            )
            zp.writestr('xl/workbook.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets>'
                '<sheet name="SheetA" sheetId="1" r:id="rId1"/>'
                '<sheet name="SheetB" sheetId="2" r:id="rId2"/>'
                '</sheets>'
                '</workbook>'
            )
            zp.writestr('xl/_rels/workbook.xml.rels',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
                '</Relationships>'
            )
            zp.writestr('xl/worksheets/sheet1.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c></row></sheetData>'
                '</worksheet>'
            )
            zp.writestr('xl/worksheets/sheet2.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="1"><c r="A1" t="s"><v>1</v></c></row></sheetData>'
                '</worksheet>'
            )
        buf.seek(0)
        xlsx_path = tmp_path / "filter_test.xlsx"
        xlsx_path.write_bytes(buf.read())

        # 1. フィルタなし
        res_all = OfficeParser.get_xlsx_content(str(xlsx_path))
        assert len(res_all) == 2
        
        # 2. SheetAのみ指定
        res_filtered = OfficeParser.get_xlsx_content(str(xlsx_path), target_sheets=["SheetA"])
        assert len(res_filtered) == 1
        assert res_filtered[0]['text'] == "S1 Val"
        assert res_filtered[0]['location'] == "SheetA!A1"

    def test_xlsx_get_sheet_summary(self, tmp_path):
        """get_sheet_summaryによる軽量サマリー取得が正しく行えるか。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zp:
            zp.writestr('xl/workbook.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets>'
                '<sheet name="SheetA" sheetId="1" r:id="rId1"/>'
                '<sheet name="SheetB" sheetId="2" r:id="rId2"/>'
                '</sheets>'
                '</workbook>'
            )
            zp.writestr('xl/_rels/workbook.xml.rels',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
                '</Relationships>'
            )
            zp.writestr('xl/worksheets/sheet1.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="1"><c r="A1"><v>100</v></c></row></sheetData>'
                '</worksheet>'
            )
            zp.writestr('xl/worksheets/sheet2.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="1"><c r="A1"><v>200</v></c><c r="B1"><v>300</v></c></row></sheetData>'
                '</worksheet>'
            )
        buf.seek(0)
        xlsx_path = tmp_path / "summary_test.xlsx"
        xlsx_path.write_bytes(buf.read())

        summary = OfficeParser.get_sheet_summary(str(xlsx_path))
        assert summary['type'] == "xlsx"
        assert summary['mode'] == "sheets"
        assert len(summary['sheets']) == 2
        assert summary['sheets'][0]['name'] == "SheetA"
        assert summary['sheets'][0]['cell_count'] == 1
        assert summary['sheets'][1]['name'] == "SheetB"
        assert summary['sheets'][1]['cell_count'] == 2
        assert summary['statistics']['sheet_count'] == 2
        assert summary['statistics']['total_cells'] == 3

    def test_pptx_parsing_logic(self, tmp_path):
        """PowerPoint (.pptx)ファイルの本文・ノートが抽出できるか。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zp:
            # スライド1
            slide_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                '<p:cSld><p:spTree><p:sp><p:txBody>'
                '<a:p><a:r><a:t>Slide 1 Title</a:t></a:r></a:p>'
                '<a:p><a:r><a:t>Slide 1 Body</a:t></a:r></a:p>'
                '</p:txBody></p:sp></p:spTree></p:cSld>'
                '</p:sld>'
            )
            # ノート1
            notes_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                '<p:cSld><p:spTree><p:sp><p:txBody>'
                '<a:p><a:r><a:t>Note Text 1</a:t></a:r></a:p>'
                '</p:txBody></p:sp></p:spTree></p:cSld>'
                '</p:notes>'
            )
            zp.writestr('ppt/slides/slide1.xml', slide_xml)
            zp.writestr('ppt/notesSlides/notesSlide1.xml', notes_xml)

        buf.seek(0)
        pptx_path = tmp_path / "test.pptx"
        pptx_path.write_bytes(buf.read())

        results = OfficeParser.get_pptx_content(str(pptx_path))
        
        # 本文とノートの両方が抽出できていること
        assert len(results) == 3
        
        texts = [r['text'] for r in results]
        assert "Slide 1 Title" in texts
        assert "Slide 1 Body" in texts
        assert "Note Text 1" in texts

        locations = [r['location'] for r in results]
        assert "スライド 1 P.1" in locations
        assert "スライド 1 (ノート) P.1" in locations
