import concurrent.futures
from dataclasses import dataclass, field
import os
import re
import threading
import fnmatch
from typing import Any, Callable, Dict, List, Optional

from src.grep.office_parser import OfficeParser


@dataclass
class GrepResult:
    """Grep検索の単一ヒット結果を保持するデータクラス"""
    file_path: str
    line_content: str
    line_number: int = 0  # 従来の行番号
    location_display: str = ""  # GUI表示用の位置情報 (例: "Sheet1!A5")
    metadata: Dict[str, Any] = field(default_factory=dict)  # 拡張用メタデータ

class GrepEngine:
    """
    外部モジュールに依存せず、Python標準ライブラリのみで構成されたGrepエンジンクラス。
    マルチスレッドによる並列スキャンと、効率的な文字コード推測をサポートします。
    """

    def __init__(
        self,
        max_threads: int = 4,
        exclude_dirs: Optional[List[str]] = None,
        exclude_exts: Optional[List[str]] = None,
        encodings: Optional[List[str]] = None,
    ):
        self.max_threads = max_threads
        self._stop_event = threading.Event()
        self.exclude_dirs = self._normalize_dirs(exclude_dirs)
        self.exclude_exts = self._normalize_extensions(exclude_exts)
        self.encodings = encodings if encodings is not None else ['utf-8', 'cp932', 'shift_jis', 'euc_jp', 'iso-2022-jp', 'utf-16']

    def stop(self) -> None:
        """検索を中断します。スレッドセーフにイベントを発行します。"""
        self._stop_event.set()

    def search(
        self,
        target_dir: str,
        search_text: str,
        regex_mode: bool = False,
        ignore_case: bool = False,
        whole_word: bool = False,
        exclude_dirs: Optional[List[str]] = None,
        exclude_exts: Optional[List[str]] = None,
        exclude_file_patterns: Optional[List[str]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_result: Optional[Callable[[GrepResult], None]] = None,
        on_complete: Optional[Callable[[int], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> int:
        """
        指定されたディレクトリ内を再帰的に検索します。
        
        Args:
            target_dir: 検索対象ディレクトリ
            search_text: 検索文字列（または正規表現パターン）
            regex_mode: 正規表現として扱うかどうか
            ignore_case: 大文字小文字を区別しない
            whole_word: 単語単位で検索する
            exclude_dirs: 除外するディレクトリ名のリスト (例: ['.git', 'node_modules'])
            exclude_exts: 除外する拡張子のリスト (例: ['.log', '.tmp'])
            on_progress: (完了ファイル数, 総ファイル数) を通知するコールバック
            on_result: ヒットした GrepResult を通知するコールバック
            on_complete: 合計ヒット数を通知するコールバック
            
        Returns:
            int: 合計ヒット数
        """
        # 前回の停止状態をクリアし、常に新しく開始できるようにする
        self._stop_event.clear()

        effective_dirs = self._normalize_dirs(exclude_dirs) if exclude_dirs is not None else self.exclude_dirs
        effective_exts = self._normalize_extensions(exclude_exts) if exclude_exts is not None else self.exclude_exts
        effective_file_patterns = [p for p in (exclude_file_patterns or []) if p]

        hit_count = 0
        all_files = self._collect_files(target_dir, effective_dirs, effective_exts, effective_file_patterns, on_error)
        total_files = len(all_files)

        # 正規表現パターンの事前コンパイル
        pattern = None
        re_flags = re.IGNORECASE if ignore_case else 0
        actual_search_text = search_text

        if whole_word and not regex_mode:
            # 単語単位(非正規表現)の場合は、正規表現の \b を使うために内部的に正規表現化する
            actual_search_text = r'\b' + re.escape(search_text) + r'\b'
            regex_mode = True

        if regex_mode:
            try:
                # 単語単位かつ正規表現の場合は、ユーザーのパターンを \b で囲む
                final_pattern = r'\b' + actual_search_text + r'\b' if (whole_word and not actual_search_text.startswith(r'\b')) else actual_search_text
                pattern = re.compile(final_pattern, re_flags)
            except re.error as e:
                raise ValueError(f"Invalid regular expression: {e}")

        # ThreadPoolExecutorによる並列読み込み
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {
                executor.submit(self._scan_file, f, actual_search_text, regex_mode, ignore_case, pattern, on_error): f
                for f in all_files
            }

            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if self._stop_event.is_set():
                    # 中断時は残りのタスク完了を待たずにループを抜ける
                    break

                try:
                    results = future.result()
                    for res in results:
                        hit_count += 1
                        if on_result:
                            on_result(res)
                except Exception as e:
                    if on_error:
                        on_error("Error occurred during file scanning task", e)

                if on_progress:
                    on_progress(i + 1, total_files)

        if on_complete:
            on_complete(hit_count)

        return hit_count

    def _collect_files(
        self,
        target_dir: str,
        exclude_dirs: Optional[List[str]] = None,
        exclude_exts: Optional[List[str]] = None,
        exclude_file_patterns: Optional[List[str]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> List[str]:
        """検索対象となるファイルのリストを収集します。"""
        file_list = []
        dir_excludes = set(exclude_dirs) if exclude_dirs else set()
        ext_excludes = set(self._normalize_extensions(exclude_exts)) if exclude_exts else set()
        patterns = [p for p in (exclude_file_patterns or [])]

        for root, dirs, files in os.walk(target_dir):
            if self._stop_event.is_set():
                break

            # 除外ディレクトリのフィルタリング (in-place modification)
            if dir_excludes:
                dirs[:] = [d for d in dirs if d not in dir_excludes]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ext_excludes:
                    continue
                # ファイル名パターンによる除外 (basename に対して fnmatch を使う)
                if patterns:
                    skip = False
                    for pat in patterns:
                        try:
                            if fnmatch.fnmatch(file, pat):
                                skip = True
                                break
                        except Exception as e:
                            if on_error:
                                on_error(f"Invalid exclude file pattern '{pat}'", e)
                            continue
                    if skip:
                        continue
                file_list.append(os.path.join(root, file))
        return file_list

    def _scan_file(
        self,
        file_path: str,
        search_text: str,
        regex_mode: bool,
        ignore_case: bool,
        pattern: Optional[re.Pattern] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> List[GrepResult]:
        """単一のファイルをスキャンしてヒットした行を返します。"""
        # 中断チェック
        if self._stop_event.is_set():
            return []

        results = []
        ext = os.path.splitext(file_path)[1].lower()

        # Officeファイルの処理
        if ext in ('.docx', '.docm', '.xlsx', '.xlsm'):
            office_data = OfficeParser.extract_content(file_path, on_error)
            if office_data:
                for item in office_data:
                    line = item.get("text", "")
                    location = item.get("location", "Unknown")
                    meta = item.get("metadata", {})
                    
                    if self._check_hit(line, search_text, regex_mode, ignore_case, pattern):
                        results.append(GrepResult(
                            file_path=file_path,
                            line_content=line,
                            location_display=location,
                            metadata={"office_type": ext, **meta}
                        ))
                return results

        # 通常のテキストファイルの処理 (メモリ効率に優れたストリーム読み込み)
        try:
            # 1. バイナリ判定 (Null Byte Check)
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                if b'\x00' in header:
                    return [] # バイナリと判定してスキップ

            # 2. エンコーディング試行とストリーム検索
            for enc in self.encodings:
                try:
                    with open(file_path, 'r', encoding=enc, errors='strict') as f:
                        for i, line in enumerate(f, 1):
                            if self._check_hit(line, search_text, regex_mode, ignore_case, pattern):
                                results.append(GrepResult(
                                    file_path=file_path,
                                    line_content=line.rstrip(),
                                    line_number=i
                                ))
                    return results # 成功したら終了
                except (UnicodeDecodeError, LookupError):
                    continue
        except (PermissionError, OSError) as e:
            if on_error:
                on_error(f"Error accessing file {file_path}", e)

        return []

    def _normalize_dirs(self, exclude_dirs: Optional[List[str]]) -> List[str]:
        if exclude_dirs is None:
            return []
        return [str(item).strip() for item in exclude_dirs if str(item).strip()]

    def _normalize_extensions(self, exclude_exts: Optional[List[str]]) -> List[str]:
        if exclude_exts is None:
            return []
        normalized: List[str] = []
        for item in exclude_exts:
            ext = str(item).strip()
            if not ext:
                continue
            if not ext.startswith('.'):
                ext = f'.{ext}'
            normalized.append(ext.lower())
        return normalized

    def _check_hit(self, line: str, search_text: str, regex_mode: bool, ignore_case: bool, pattern: Optional[re.Pattern] = None) -> bool:
        """指定された行が検索テキストにマッチするか判定します。"""
        if regex_mode and pattern:
            return bool(pattern.search(line))
        
        if ignore_case:
            return search_text.lower() in line.lower()
        
        return search_text in line
