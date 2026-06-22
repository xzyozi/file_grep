from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable

from src.tk_gui.base.base_frame_gui import BaseFrameGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication

from src.grep.presets import SearchPresets


class PhraseListComponent(BaseFrameGUI):
    """
    定型検索パターン（スニペット）を管理・表示するコンポーネント。
    """

    def __init__(
        self,
        master: tk.Misc,
        app_instance: BaseApplication,
        on_select: Callable[[str, str, bool], None]
    ) -> None:
        super().__init__(master, app_instance)
        self.on_select = on_select
        self._create_widgets()

        # 言語変更イベントの購読
        self.app.event_dispatcher.subscribe('LANGUAGE_CHANGED', self._refresh_labels)

    def _create_widgets(self) -> None:
        columns = ('label', 'pattern')
        # show='tree headings' にして、親子の階層関係を表示可能にする
        self.tree = ttk.Treeview(self, columns=columns, show='tree headings', selectmode='browse')

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
        self.tree.heading('#0', text=_t('category') if _t('category') != 'category' else 'Category')
        self.tree.heading('label', text=_t('snippet_label'))
        self.tree.heading('pattern', text=_t('pattern_regex'))

        self.tree.column('#0', width=150, anchor=tk.W)
        self.tree.column('label', width=150, anchor=tk.W)
        self.tree.column('pattern', width=250, anchor=tk.W)

    def _refresh_list(self) -> None:
        """UIの表示を最新のスニペットデータで更新します。"""
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        grouped_presets = SearchPresets.get_all_grouped()
        for cat_info in grouped_presets:
            category_name = cat_info.get("category", "Other")
            items = cat_info.get("items", [])

            # 親ノードを追加 (値は空, ツリー表示部にカテゴリ名を表示)
            parent_id = self.tree.insert('', tk.END, text=category_name, open=True)

            for label, pattern, is_regex in items:
                # 子ノードを追加 (値にはラベルとパターンを格納)
                self.tree.insert(parent_id, tk.END, text='', values=(label, pattern))

    def _on_double_click(self, event: tk.Event) -> None:
        """項目がダブルクリックされた時、そのパターンを検索欄にセットします。"""
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        values = self.tree.item(item_id, 'values')
        # 親ノード（値がないもの）は無視
        if not values or len(values) < 2:
            return

        label, pattern = values[0], values[1]

        # is_regex の判定
        found_pat, found_reg = SearchPresets.get_by_label(label)
        is_regex = found_reg if found_pat == pattern else True

        self.on_select(label, pattern, is_regex)
