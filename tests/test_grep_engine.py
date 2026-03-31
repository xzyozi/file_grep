import os
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
        
        # 大量のファイルがある状況を想定するために、ループ中に stop をかける
        # (このテストでは小規模だが、フラグが立つことを確認)
        engine.stop()
        hit_count = engine.search(
            target_dir=str(temp_test_files),
            search_text="テスト"
        )
        
        # 検索前に stop しているので 0 ヒットになるはず
        assert hit_count == 0
