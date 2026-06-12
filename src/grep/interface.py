from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Protocol

if TYPE_CHECKING:
    from src.grep.engine import GrepResult

class GrepEngineProtocol(Protocol):
    """
    Grepエンジンの共通インターフェース定義。
    実体(GrepEngine)とモック(MockGrepEngine)の両方で共通して使用します。
    """
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
        ...

    def stop(self) -> None:
        ...


class FileParserProtocol(Protocol):
    """
    ファイルからコンテンツを抽出するパーサーの共通インターフェース。
    """
    def extract_content(
        self,
        file_path: str,
        on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> List[Dict[str, Any]]:
        ...

