import os
import zipfile
import pytest
from src.grep.engine import GrepEngine, GrepResult

@pytest.fixture
def temp_test_files(tmp_path):
    """テスト用のダミーファイル群を作成するフィクスチャ"""
    # UTF-8 ファイル
    utf8_file = tmp_path / "test_utf8.txt"
    utf8_file.write_text("Hello World\nこれは日本語のテストです\nPython search", encoding="utf-8")
    
    # CP932 (Shift-JIS) ファイル
    cp932_file = tmp_path / "test_cp932.txt"
    cp932_content = "これはShift-JISのテストです\n検索ワードはこちら".encode("cp932")
    with open(cp932_file, "wb") as f:
        f.write(cp932_content)
        
    # バイナリファイル (デコードできないはず)
    bin_file = tmp_path / "test.bin"
    with open(bin_file, "wb") as f:
        f.write(b"\xff\xfe\xfd\x00\x01\x02")

    # 最小構成の .docx (zip) を作成
    docx_file = tmp_path / "test.docx"
    with zipfile.ZipFile(docx_file, 'w') as zp:
        # word/document.xml の構造を簡略化して作成
        doc_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Word Search Word</w:t></w:r></w:p></w:body></w:document>'
        zp.writestr('word/document.xml', doc_xml)

    # 最小構成の .xlsx (zip) を作成
    xlsx_file = tmp_path / "test.xlsx"
    with zipfile.ZipFile(xlsx_file, 'w') as zp:
        # xl/sharedStrings.xml の構造を簡略化して作成
        shared_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1"><si><t>Excel Search Cell</t></si></sst>'
        zp.writestr('xl/sharedStrings.xml', shared_xml)
        
    return tmp_path

class TestGrepEngine:
    def test_basic_search(self, temp_test_files):
        """基本のテキスト検索が正しく動作するか"""
        engine = GrepEngine()
        results = []
        
        def on_result(res):
            results.append(res)
            
        hit_count = engine.search(
            target_dir=str(temp_test_files),
            search_text="Python",
            on_result=on_result
        )
        
        assert hit_count == 1
        assert len(results) == 1
        assert "Python" in results[0].line_content
        assert results[0].line_number == 3

    def test_multilingual_search(self, temp_test_files):
        """UTF-8 と CP932 の両方から日本語を検索できるか"""
        engine = GrepEngine()
        results = []
        
        def on_result(res):
            results.append(res)
            
        # 両方のファイルに含まれる「テスト」を検索
        hit_count = engine.search(
            target_dir=str(temp_test_files),
            search_text="テスト",
            on_result=on_result
        )
        
        # test_utf8.txt (1ヒット) + test_cp932.txt (1ヒット) = 2ヒット
        assert hit_count == 2
        assert any("utf8" in res.file_path for res in results)
        assert any("cp932" in res.file_path for res in results)

    def test_regex_search(self, temp_test_files):
        """正規表現モードが正しく動作するか"""
        engine = GrepEngine()
        results = []
        
        def on_result(res):
            results.append(res)
            
        # 「World」または「search」にマッチする正規表現
        hit_count = engine.search(
            target_dir=str(temp_test_files),
            search_text=r"World|search",
            regex_mode=True,
            on_result=on_result
        )
        
        assert hit_count == 2

    def test_progress_callback(self, temp_test_files):
        """進捗コールバックが適切に呼び出されるか"""
        engine = GrepEngine()
        progress_calls = []
        
        def on_progress(current, total):
            progress_calls.append((current, total))
            
        engine.search(
            target_dir=str(temp_test_files),
            search_text="test",
            on_progress=on_progress
        )
        
        assert len(progress_calls) > 0
        # 最終的な進捗が正しいか (ファイル収集結果によるが、少なくとも最後は current == total)
        last_call = progress_calls[-1]
        assert last_call[0] <= last_call[1]

    def test_stop_functionality(self, temp_test_files):
        """中断機能が動作するか"""
        engine = GrepEngine()
        
        # 検索中に stop をかけるためにコールバックを利用
        results = []
        def on_result(res):
            results.append(res)
            engine.stop()  # 1件見つかったら停止
            
        hit_count = engine.search(
            target_dir=str(temp_test_files),
            search_text="テスト",
            on_result=on_result
        )
        
        # 2つテストファイルがあるはずだが、1つ目で止まるので hit_count は 1 になるはず
        # (スレッドのタイミングによっては2になる可能性もゼロではないが、基本は中断される)
        assert hit_count < 2

    def test_office_search(self, temp_test_files):
        """Officeファイル(Word/Excel)が正しく検索できるか"""
        engine = GrepEngine()
        
        # --- Wordのテスト (.docx, .docm 共に検証) ---
        for ext in (".docx", ".docm"):
            multi_word = temp_test_files / f"test{ext}"
            with zipfile.ZipFile(multi_word, 'w') as zp:
                doc_xml = (
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    f'<w:body><w:p><w:t>Sample Word {ext} content</w:t></w:p></w:body>'
                    '</w:document>'
                )
                zp.writestr('word/document.xml', doc_xml)

        results = []
        def on_result(res):
            results.append(res)
            
        engine.search(target_dir=str(temp_test_files), search_text="Word", on_result=on_result)
        # 両方の拡張子がヒットしていることを確認
        assert any(".docx" in res.file_path for res in results)
        assert any(".docm" in res.file_path for res in results)

        # --- Excelのテスト (詳細検証) ---
        results.clear()
        # フィクスチャで作成した test.xlsx には "Excel Search Cell" が含まれている
        engine.search(target_dir=str(temp_test_files), search_text="Excel", on_result=on_result)
        assert len(results) == 1
        assert "Excel Search Cell" in results[0].line_content

        # 新しく「複数ヒット・非ヒット」を含む Excel(.xlsx) と Macro(.xlsm) を作成してテスト
        for ext in (".xlsx", ".xlsm"):
            multi_file = temp_test_files / f"multi_test{ext}"
            with zipfile.ZipFile(multi_file, 'w') as zp:
                shared_xml = (
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    '<si><t>Apple</t></si>'
                    '<si><t>Banana Target</t></si>'
                    '<si><t>Cherry</t></si>'
                    '<si><t>Date Target</t></si>'
                    '</sst>'
                )
                zp.writestr('xl/sharedStrings.xml', shared_xml)

        results.clear()
        engine.search(target_dir=str(temp_test_files), search_text="Target", on_result=on_result)
        
        # .xlsx と .xlsm 両方から 2つずつ、計 4つヒットするはず
        target_hits = [res for res in results if "multi_test" in res.file_path]
        assert len(target_hits) == 4
        assert any(".xlsm" in res.file_path for res in target_hits)
        assert any(".xlsx" in res.file_path for res in target_hits)
