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
