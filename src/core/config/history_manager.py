from __future__ import annotations

import json
import os
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    検索履歴の保存・読み込みを管理するクラス。
    history.json への永続化を担当します。
    """

    def __init__(self, filename: str = "history.json", max_items: int = 50) -> None:
        # プロジェクトルート (src の二階層上) を基準に絶対パスを構築
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.filepath = os.path.join(root_dir, filename)
        self.max_items = max_items
        self.history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """履歴ファイルをロードします。"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load history from {self.filepath}: {e}")
        return []

    def add_entry(self, keyword: str, directory: str, is_regex: bool) -> None:
        """新しい検索履歴を追加し、重複を除去してファイルに保存します。"""
        new_entry = {
            'keyword': keyword,
            'directory': directory,
            'is_regex': is_regex
        }
        
        # 重複チェック（同一内容なら一旦削除）
        self.history = [h for h in self.history if not (
            h['keyword'] == keyword and 
            h['directory'] == directory and 
            h['is_regex'] == is_regex
        )]
        
        # 先頭に挿入
        self.history.insert(0, new_entry)
        
        # 件数制限
        if len(self.history) > self.max_items:
            self.history = self.history[:self.max_items]
            
        self.save_history()

    def get_all(self) -> List[Dict[str, Any]]:
        """全履歴を取得します。"""
        return self.history

    def save_history(self) -> None:
        """現在の履歴をファイルに書き出します。"""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4)
            logger.info(f"History saved to {self.filepath}")
        except OSError as e:
            logger.error(f"Failed to save history: {e}")
