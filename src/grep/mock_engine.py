import time
import random
from typing import Callable, List, Optional
from dataclasses import dataclass

@dataclass
class GrepResult:
    """Grep検索の単一ヒット結果を保持するデータクラス"""
    file_path: str
    line_number: int
    line_content: str

class MockGrepEngine:
    """
    GUI開発用のモックGrepエンジン。
    実際のスキャンは行わず、ダミーデータを生成して進捗と結果を返します。
    """
    def __init__(self):
        self.is_running = False

    def search(
        self,
        target_dir: str,
        search_text: str,
        regex_mode: bool = False,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_result: Optional[Callable[[GrepResult], None]] = None,
        on_complete: Optional[Callable[[int], None]] = None
    ) -> None:
        """
        擬似的な検索を開始します。
        
        Args:
            target_dir: 検索対象ディレクトリ (無視されます)
            search_text: 検索文字列
            regex_mode: 正規表現モード
            on_progress: (完了数, 総ファイル数) を受け取るコールバック
            on_result: 見つかった GrepResult を受け取るコールバック
            on_complete: 合計ヒット数を受け取るコールバック
        """
        self.is_running = True
        total_files = 100
        hit_count = 0

        # モックなので、それっぽいダミーデータを生成
        dummy_files = [
            f"c:/users/project/src/module_{i}.py" for i in range(total_files)
        ]

        for i, file_path in enumerate(dummy_files):
            if not self.is_running:
                break

            # 進捗通知
            if on_progress:
                on_progress(i + 1, total_files)

            # 一定確率でヒットさせる
            if random.random() < 0.1:  # 10%の確率
                result = GrepResult(
                    file_path=file_path,
                    line_number=random.randint(1, 100),
                    line_content=f"Found '{search_text}' in dummy content."
                )
                hit_count += 1
                if on_result:
                    on_result(result)

            # 少し待機してリアルな動作を演出
            time.sleep(0.05)

        self.is_running = False
        if on_complete:
            on_complete(hit_count)

    def stop(self):
        """検索を中断します。"""
        self.is_running = False
