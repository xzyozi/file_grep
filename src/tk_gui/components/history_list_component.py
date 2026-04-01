from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any, Callable, Dict, List

from src.tk_gui.base.base_frame_gui import BaseFrameGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class HistoryListComponent(BaseFrameGUI):
    """
    過去の検索履歴を表示・管理するコンポーネント。
    """

    def __init__(self, master: tk.Misc, app_instance: BaseApplication, on_select: Callable[[str, str, bool], None]) -> None:
        super().__init__(master, app_instance)
        self.on_select = on_select
        self._history_items: List[Dict[str, Any]] = []
        self._create_widgets()
        
        # 言語変更イベントの購読
        self.app.event_dispatcher.subscribe('LANGUAGE_CHANGED', self._refresh_labels)

    def _create_widgets(self) -> None:
        columns = ('keyword', 'directory', 'regex')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')

        self.vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<Double-1>', self._on_double_click)
        
        # 初期ラベル設定
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        """カラムヘッダーのテキストを更新します。"""
        _t = self.app.translator
        self.tree.heading('keyword', text=_t('keyword'))
        self.tree.heading('directory', text=_t('directory'))
        self.tree.heading('regex', text=_t('regex_short'))
        
        self.tree.column('keyword', width=150, anchor=tk.W)
        self.tree.column('directory', width=250, anchor=tk.W)
        self.tree.column('regex', width=60, anchor=tk.CENTER)

    def add_history(self, keyword: str, directory: str, is_regex: bool) -> None:
        """履歴項目を追加します。"""
        # 重複チェック（単純化のため最新を一番上に）
        item = {'keyword': keyword, 'directory': directory, 'is_regex': is_regex}
        self._history_items.insert(0, item)
        self._refresh_list()

    def _refresh_list(self) -> None:
        """現在の履歴リストでTreeviewを再描画します。"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for item in self._history_items:
            self.tree.insert('', tk.END, values=(
                item['keyword'],
                item['directory'],
                'YES' if item['is_regex'] else 'NO'
            ))

    def _on_double_click(self, event: tk.Event) -> None:
        """項目がダブルクリックされた時、その検索条件をメイン画面に適用します。"""
        selected = self.tree.selection()
        if not selected:
            return

        index = self.tree.index(selected[0])
        if 0 <= index < len(self._history_items):
            item = self._history_items[index]
            self.on_select(item['keyword'], item['directory'], item['is_regex'])
