from __future__ import annotations

import random
import threading
import time
from typing import Callable, Optional

from src.grep.engine import GrepResult


class MockGrepEngine:
    """
    GUI開発用のモックエンジン。
    Protocol(GrepEngineProtocol)に準拠したダミー結果を非同期に返します。
    """
    def __init__(self, max_threads: int = 1):
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """モックの検索を停止します。"""
        self._stop_event.set()

    def search(
        self,
        target_dir: str,
        search_text: str,
        regex_mode: bool = False,
        ignore_case: bool = False,
        whole_word: bool = False,
        exclude_dirs: Optional[List[str]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_result: Optional[Callable[[GrepResult], None]] = None,
        on_complete: Optional[Callable[[int], None]] = None
    ) -> int:
        """ダミーの結果を生成して返します（ウェイトを挟む）。"""
        self._stop_event.clear()

        # モック用のダミーファイル数
        total_files = 20
        hit_count = 0

        for i in range(1, total_files + 1):
            if self._stop_event.is_set():
                break

            # 適度なウェイト（0.1〜0.5秒）を挟んでUIでのプログレスバーを再現しやすくする
            time.sleep(random.uniform(0.1, 0.3))

            # 2割の確率でヒットさせる
            if random.random() < 0.2:
                hit_count += 1
                if on_result:
                    res = GrepResult(
                        file_path=f"mock_data/sample_file_{i}.txt",
                        line_content=f"This is a mock hit containing '{search_text}' at index {i}",
                        line_number=random.randint(1, 100)
                    )
                    on_result(res)

            if on_progress:
                on_progress(i, total_files)

        if on_complete:
            on_complete(hit_count)

        return hit_count
