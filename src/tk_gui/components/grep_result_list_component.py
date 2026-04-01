from __future__ import annotations

import os
import subprocess
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List

from src.tk_gui.base.base_frame_gui import BaseFrameGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication
    from src.grep.engine import GrepResult


class GrepResultListComponent(BaseFrameGUI):
    """
    検索結果を一覧表示するコンポーネント。
    """

    def __init__(self, master: tk.Misc, app_instance: BaseApplication) -> None:
        super().__init__(master, app_instance)
        self._results: List[GrepResult] = []
        self._create_widgets()

        # 言語変更イベントの購読
        self.app.event_dispatcher.subscribe('LANGUAGE_CHANGED', self._refresh_labels)

    def _create_widgets(self) -> None:
        columns = ('file', 'line', 'content')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')

        self.vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

        # 初期ラベル設定
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        """カラムヘッダーのテキストを更新します。"""
        _t = self.app.translator
        self.tree.heading('file', text=_t('file_name'))
        self.tree.heading('line', text=_t('line_no'))
        self.tree.heading('content', text=_t('content'))

        self.tree.column('file', width=200, anchor=tk.W)
        self.tree.column('line', width=60, anchor=tk.CENTER)
        self.tree.column('content', width=500, anchor=tk.W)

    def add_result(self, result: GrepResult) -> None:
        """結果をリストに追加します。"""
        self._results.append(result)
        self.tree.insert('', tk.END, values=(
            os.path.basename(result.file_path),
            result.line_number,
            result.line_content
        ))

    def clear(self) -> None:
        """リストをクリアします。"""
        self._results.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _on_double_click(self, event: tk.Event) -> None:
        """項目がダブルクリックされた時、ファイルを開きます。"""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        index = self.tree.index(selected_item[0])
        if 0 <= index < len(self._results):
            file_path = self._results[index].file_path
            if os.path.exists(file_path):
                os.startfile(file_path)

    def _on_right_click(self, event: tk.Event) -> None:
        """右クリックメニューの表示。"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            _t = self.app.translator

            menu.add_command(label=_t('open_file'), command=self._open_selected_file)
            menu.add_command(label=_t('open_folder'), command=self._open_folder)
            menu.tk_popup(event.x_root, event.y_root)

    def _open_selected_file(self) -> None:
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected[0])
            os.startfile(self._results[index].file_path)

    def _open_folder(self) -> None:
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected[0])
            path = self._results[index].file_path
            subprocess.run(['explorer', '/select,', os.path.normpath(path)])
