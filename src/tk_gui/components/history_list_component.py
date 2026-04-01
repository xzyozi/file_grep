from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.tk_gui.base.base_frame_gui import BaseFrameGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class HistoryListComponent(BaseFrameGUI):
    """
    過去の検索履歴（キーワード、ディレクトリ、設定）を表示・管理するコンポーネント。
    """

    def __init__(self, master: tk.Misc, app_instance: BaseApplication, on_select: Callable[[str, str, bool], None]) -> None:
        super().__init__(master, app_instance)
        self.on_select = on_select
        self._history_items: List[Dict[str, Any]] = []
        self._create_widgets()

    def _create_widgets(self) -> None:
        # 履歴表示用の Treeview (キーワード、ディレクトリ、正規表現)
        columns = ('keyword', 'directory', 'regex')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')

        self.tree.heading('keyword', text='Keyword')
        self.tree.heading('directory', text='Directory')
        self.tree.heading('regex', text='Regex')

        self.tree.column('keyword', width=150, anchor=tk.W)
        self.tree.column('directory', width=300, anchor=tk.W)
        self.tree.column('regex', width=50, anchor=tk.CENTER)

        self.vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # ダブルクリックでその履歴を適用するイベント
        self.tree.bind('<Double-1>', self._on_double_click)

    def add_history(self, keyword: str, directory: str, is_regex: bool) -> None:
        """新しい検索履歴を追加します。"""
        # 重複チェック（同一条件なら先頭へ移動）
        for i, item in enumerate(self._history_items):
            if item['keyword'] == keyword and item['directory'] == directory and item['is_regex'] == is_regex:
                self._history_items.pop(i)
                break
        
        self._history_items.insert(0, {
            'keyword': keyword,
            'directory': directory,
            'is_regex': is_regex
        })
        self.refresh_list()

    def refresh_list(self) -> None:
        """UIの表示を最新の履歴データで更新します。"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for item in self._history_items:
            regex_str = 'Yes' if item['is_regex'] else 'No'
            self.tree.insert('', tk.END, values=(
                item['keyword'],
                item['directory'],
                regex_str
            ))

    def _on_double_click(self, event: tk.Event) -> None:
        """項目がダブルクリックされた時、その検索条件をメイン画面に適用するようイベントを発火します。"""
        selected = self.tree.selection()
        if not selected:
            return

        index = self.tree.index(selected[0])
        if 0 <= index < len(self._history_items):
            item = self._history_items[index]
            self.on_select(item['keyword'], item['directory'], item['is_regex'])
