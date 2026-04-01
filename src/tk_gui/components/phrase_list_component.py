from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable, Dict, List

from src.tk_gui.base.base_frame_gui import BaseFrameGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class PhraseListComponent(BaseFrameGUI):
    """
    定型検索パターン（スニペット）を管理・表示するコンポーネント。
    """

    def __init__(
        self,
        master: tk.Misc,
        app_instance: BaseApplication,
        on_select: Callable[[str, str], None]
    ) -> None:
        super().__init__(master, app_instance)
        self.on_select = on_select
        # 固定のプリセットスニペット
        self._snippets: List[Dict[str, str]] = [
            {'label': 'Python: Function', 'pattern': r'^def\s+\w+\('},
            {'label': 'Python: Class', 'pattern': r'^class\s+\w+[:\(]'},
            {'label': 'Import statements', 'pattern': r'^import\s+|^from\s+'},
            {'label': 'TODO Comments', 'pattern': r'#\s*TODO[:\s]'},
            {'label': 'Email address', 'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'},
        ]
        self._create_widgets()

        # 言語変更イベントの購読
        self.app.event_dispatcher.subscribe('LANGUAGE_CHANGED', self._refresh_labels)

    def _create_widgets(self) -> None:
        columns = ('label', 'pattern')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')

        self.vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<Double-1>', self._on_double_click)
        self._refresh_list()

        # 初期ラベル設定
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        """カラムヘッダーのテキストを更新します。"""
        _t = self.app.translator
        self.tree.heading('label', text=_t('snippet_label'))
        self.tree.heading('pattern', text=_t('pattern_regex'))

        self.tree.column('label', width=150, anchor=tk.W)
        self.tree.column('pattern', width=250, anchor=tk.W)

    def _refresh_list(self) -> None:
        """UIの表示を最新のスニペットデータで更新します。"""
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for snippet in self._snippets:
            self.tree.insert('', tk.END, values=(
                snippet['label'],
                snippet['pattern']
            ))

    def _on_double_click(self, event: tk.Event) -> None:
        """項目がダブルクリックされた時、そのパターンを検索欄にセットします。"""
        selected = self.tree.selection()
        if not selected:
            return

        index = self.tree.index(selected[0])
        if 0 <= index < len(self._snippets):
            snippet = self._snippets[index]
            self.on_select(snippet['label'], snippet['pattern'])
