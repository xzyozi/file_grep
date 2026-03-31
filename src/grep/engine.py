from __future__ import annotations
import os
import re
import concurrent.futures
from dataclasses import dataclass
from typing import Callable, List, Optional, Any

@dataclass
class GrepResult:
    """Grep検索の単一ヒット結果を保持するデータクラス"""
    file_path: str
    line_number: int
    line_content: str

class GrepEngine:
    """
    外部モジュールに依存せず、Python標準ライブラリのみで構成されたGrepエンジンクラス。
    マルチスレッドによる並列スキャンと、効率的な文字コード推測をサポートします。
    """

    # 検索対象から除外する一般的なバイナリ拡張子
    BINARY_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.pyc', '.pyo',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.pdf',
        '.zip', '.tar', '.gz', '.rar', '.7z', '.class', '.obj', '.o'
    }

    # 試行する文字コードのリスト（一般的なものを優先）
    ENCODINGS = ['utf-8', 'cp932', 'shift_jis', 'euc_jp', 'iso-2022-jp', 'utf-16']

    def __init__(self, max_threads: int = 4):
        self.max_threads = max_threads
        self._stop_requested = False

    def stop(self) -> None:
        """検索を中断します。"""
        self._stop_requested = True

    def search(
        self,
        target_dir: str,
        search_text: str,
        regex_mode: bool = False,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_result: Optional[Callable[[GrepResult], None]] = None,
        on_complete: Optional[Callable[[int], None]] = None
    ) -> int:
        """
        指定されたディレクトリ内を再帰的に検索します。
        
        Args:
            target_dir: 検索対象ディレクトリ
            search_text: 検索文字列（または正規表現パターン）
            regex_mode: 正規表現として扱うかどうか
            on_progress: (完了ファイル数, 総ファイル数) を通知するコールバック
            on_result: ヒットした GrepResult を通知するコールバック
            on_complete: 合計ヒット数を通知するコールバック
            
        Returns:
            int: 合計ヒット数
        """
        # 検索開始前に既に中断リクエストがあれば即座に終了
        if self._stop_requested:
            if on_complete:
                on_complete(0)
            return 0

        self._stop_requested = False
        all_files = self._collect_files(target_dir)
        total_files = len(all_files)
        hit_count = 0

        # 正規表現パターンの事前コンパイル
        pattern = None
        if regex_mode:
            try:
                pattern = re.compile(search_text)
            except re.error:
                # 不正な正規表現の場合は通常の文字列として扱うかエラーにするか検討が必要だが、
                # ここでは安全のため通常の検索にフォールバック、または空の結果を返す
                regex_mode = False

        # ThreadPoolExecutorによる並列読み込み
        # I/Oバウンドな処理であるため、スレッドによる並列化が有効
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {
                executor.submit(self._scan_file, f, search_text, regex_mode, pattern): f 
                for f in all_files
            }
            
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if self._stop_requested:
                    # キャンセル時は即座に終了するが、実行中のフューチャは完了を待つ必要がある
                    break
                
                try:
                    results = future.result()
                    for res in results:
                        hit_count += 1
                        if on_result:
                            on_result(res)
                except Exception:
                    # 個別のファイル読み取りエラーはスキップ
                    pass

                if on_progress:
                    on_progress(i + 1, total_files)

        if on_complete:
            on_complete(hit_count)
            
        return hit_count

    def _collect_files(self, target_dir: str) -> List[str]:
        """検索対象となるファイルのリストを収集します。"""
        file_list = []
        for root, _, files in os.walk(target_dir):
            if self._stop_requested:
                break
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in self.BINARY_EXTENSIONS:
                    file_list.append(os.path.join(root, file))
        return file_list

    def _scan_file(
        self, 
        file_path: str, 
        search_text: str, 
        regex_mode: bool, 
        pattern: Optional[re.Pattern] = None
    ) -> List[GrepResult]:
        """単一のファイルをスキャンしてヒットした行を返します。"""
        results = []
        
        # バイナリモードで読み込んで、手動で文字コード試行を行う（chardet不使用）
        raw_data = None
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
        except (PermissionError, OSError):
            return []

        if not raw_data:
            return []

        # エンコーディングを順番に試す
        content = None
        for enc in self.ENCODINGS:
            try:
                content = raw_data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # どのエンコーディングでもデコードできない場合はスキップ（バイナリ等）
            return []

        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            is_hit = False
            if regex_mode and pattern:
                if pattern.search(line):
                    is_hit = True
            else:
                if search_text in line:
                    is_hit = True
            
            if is_hit:
                results.append(GrepResult(
                    file_path=file_path,
                    line_number=i,
                    line_content=line
                ))
                
        return results
