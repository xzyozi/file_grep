import json
import os
from typing import Any, Dict, List, Optional, Tuple


class SearchPresets:
    """
    外部ファイル (presets.json) から検索パターン（スニペット）を読み込んで管理するクラス。
    """

    _presets: Optional[List[Tuple[str, str, bool]]] = None
    _presets_grouped: Optional[List[Dict[str, Any]]] = None
    # 実行場所に関わらず config/presets.json を見つけられるように絶対パスを構築
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PRESETS_FILE = os.path.join(_BASE_DIR, "config", "presets.json")

    @classmethod
    def _load_presets_if_needed(cls) -> None:
        """presets.json からデータを読み込み、_presets および _presets_grouped キャッシュを構築します。"""
        if cls._presets is not None:
            return

        cls._presets = []
        cls._presets_grouped = []
        if not os.path.exists(cls.PRESETS_FILE):
            return

        try:
            with open(cls.PRESETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cls._presets_grouped = data
                for cat_info in data:
                    items = cat_info.get('items', [])
                    for lbl, pat, is_reg in items:
                        cls._presets.append((lbl, pat, is_reg))
        except (json.JSONDecodeError, ValueError, Exception):
            # 読み込み失敗時は空のまま
            pass

    @classmethod
    def get_all(cls) -> List[Tuple[str, str, bool]]:
        """すべてのプリセットを返します。"""
        cls._load_presets_if_needed()
        return cls._presets or []

    @classmethod
    def get_all_grouped(cls) -> List[Dict[str, Any]]:
        """カテゴリ階層を維持したプリセットデータを返します。"""
        cls._load_presets_if_needed()
        return cls._presets_grouped or []

    @classmethod
    def get_by_label(cls, label: str) -> Tuple[str, bool]:
        """ラベル名から検索パターンを取得します。"""
        cls._load_presets_if_needed()
        for lbl, pat, is_reg in (cls._presets or []):
            if lbl == label:
                return pat, is_reg
        return "", False
