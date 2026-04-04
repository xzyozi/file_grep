from __future__ import annotations

from typing import Dict, List, Tuple


class SearchPresets:
    """
    再利用可能な検索パターン（スニペット）を管理するクラス。
    """

    # (ラベル名, 検索パターン, 正規表現かどうか)
    PRESETS: List[Tuple[str, str, bool]] = [
        # --- プログラミング (Python等) ---
        ("Python: Function", r"^def\s+\w+\(", True),
        ("Python: Class", r"^class\s+\w+[:\(]", True),
        ("Import statements", r"^import\s+|^from\s+", True),
        ("TODO / FIXME", r"(TODO|FIXME|HACK|NOTE):", True),
        
        # --- 構造化データ/文字列 ---
        ("JSON Key", r"\"\w+\"\s*:", True),
        ("XML Tag", r"<[^>]+>", True),
        ("Empty Line", r"^\s*$", True),
        ("Trailing Space", r"\s+$", True),
        ("UUID / GUID", r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", True),
        ("Hex Color", r"#(?:[0-9a-fA-F]{3}){1,2}\b", True),
        
        # --- ネットワーク・Web ---
        ("IPv4 Address", r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", True),
        ("URL (HTTP/HTTPS)", r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+", True),
        ("Email Address", r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", True),
        
        # --- ログ・サーバー状況 ---
        ("HTTP Error (4xx/5xx)", r" [45]\d{2} ", True),
        ("Timestamp (YYYY-MM-DD)", r"\d{4}-\d{2}-\d{2}", True),
        ("Time (HH:MM:SS)", r"\d{2}:\d{2}:\d{2}", True),
        
        # --- 日本語・文字種 ---
        ("全角文字 (含記号)", r"[^\x01-\x7E]+", True),
        ("ひらがな", r"[ぁ-ん]+", True),
        ("カタカナ", r"[ァ-ヶー]+", True),
        ("漢字", r"[\u4E00-\u9FD0]+", True),
        
        # --- その他 ---
        ("Phone Number (Japan)", r"0\d{1,4}-\d{1,4}-\d{4}", True),
    ]

    @classmethod
    def get_all(cls) -> List[Tuple[str, str, bool]]:
        """すべてのプリセットを返します。"""
        return cls.PRESETS

    @classmethod
    def get_by_label(cls, label: str) -> Tuple[str, bool]:
        """ラベル名から検索パターンを取得します。"""
        for l, p, r in cls.PRESETS:
            if l == label:
                return p, r
        return "", False
