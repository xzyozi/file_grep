import json
import os
from typing import List, Optional, Tuple


class SearchPresets:
    """
    外部ファイル (presets.json) から検索パターン（スニペット）を読み込んで管理するクラス。
    """

    _presets: Optional[List[Tuple[str, str, bool]]] = None
    PRESETS_FILE = "presets.json"

    @classmethod
    def _load_presets_if_needed(cls) -> None:
        """presets.json からデータを読み込み、_presets キャッシュを構築します。"""
        if cls._presets is not None:
            return

        cls._presets = []
        if not os.path.exists(cls.PRESETS_FILE):
            return

        try:
            with open(cls.PRESETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for cat_info in data:
                    items = cat_info.get('items', [])
                    for label, pattern, is_regex in items:
                        cls._presets.append((label, pattern, is_regex))
        except (json.JSONDecodeError, ValueError, Exception):
            # 読み込み失敗時は空のまま
            pass

    @classmethod
    def get_all(cls) -> List[Tuple[str, str, bool]]:
        """すべてのプリセットを返します。"""
        cls._load_presets_if_needed()
        return cls._presets or []

    @classmethod
    def get_by_label(cls, label: str) -> Tuple[str, bool]:
        """ラベル名から検索パターンを取得します。"""
        cls._load_presets_if_needed()
        for l, p, r in (cls._presets or []):
            if l == label:
                return p, r
        return "", False
