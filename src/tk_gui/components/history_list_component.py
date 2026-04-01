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
    history.json に保存するため HistoryManager を使用します。
    """

    def __init__(self, master: tk.Misc, app_instance: BaseApplication, on_select: Callable[[str, str, bool], None]) -> None:
        super().__init__(master, app_instance)
        self.on_select = on_select
        
        # 履歴データの読み込み
        self._history_items: List[Dict[str, Any]] = self.app.history_manager.get_all()
        
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
        
        self._refresh_labels()
        self._refresh_list()

    def _refresh_labels(self) -> None:
        """多言語ラベルのリフレッシュ。"""
        _t = self.app.translator
        self.tree.heading('keyword', text=_t('keyword'))
        self.tree.heading('directory', text=_t('directory'))
        self.tree.heading('regex', text=_t('regex_short'))
        
        self.tree.column('keyword', width=150, anchor=tk.W)
        self.tree.column('directory', width=250, anchor=tk.W)
        self.tree.column('regex', width=60, anchor=tk.CENTER)

    def add_history(self, keyword: str, directory: str, is_regex: bool) -> None:
        """履歴に項目を追加します。HistoryManager を通じて行います。"""
        self.app.history_manager.add_entry(keyword, directory, is_regex)
        
        # 表示側も最新データで更新
        self._history_items = self.app.history_manager.get_all()
        self._refresh_list()

    def _refresh_list(self) -> None:
        """現在の履歴リストでTreeviewを再描画します。"""
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        
        for hist_item in self._history_items:
            self.tree.insert('', tk.END, values=(
                hist_item['keyword'],
                hist_item['directory'],
                'YES' if hist_item['is_regex'] else 'NO'
            ))

    def _on_double_click(self, event: tk.Event) -> None:
        """項目が選択（ダブルクリック）された際の通知。"""
        selected = self.tree.selection()
        if not selected:
            return

        index = self.tree.index(selected[0])
        if 0 <= index < len(self._history_items):
            item = self._history_items[index]
            self.on_select(item['keyword'], item['directory'], item['is_regex'])
