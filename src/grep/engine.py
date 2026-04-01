from dataclasses import dataclass

@dataclass
class GrepResult:
    """Grep検索の単一ヒット結果を保持するデータクラス"""
    file_path: str
    line_number: int
    line_content: str
