from __future__ import annotations

import os
import subprocess
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Optional

from src.tk_gui.base.base_frame_gui import BaseFrameGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication
    from src.grep.engine import GrepResult


class GrepResultListComponent(BaseFrameGUI):
    """
    Grep検索の結果を表示するためのリストコンポーネント。
    """

    def __init__(self, master: tk.Misc, app_instance: BaseApplication) -> None:
        super().__init__(master, app_instance)
        self._results: list[GrepResult] = []
        self._create_widgets()

    def _create_widgets(self) -> None:
        # 結果表示用のツリービュー（ファイル名、行番号、内容を表示）
        columns = ('file', 'line', 'content')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')

        # 列の設定
        self.tree.heading('file', text='File')
        self.tree.heading('line', text='Line')
        self.tree.heading('content', text='Content')

        self.tree.column('file', width=200, anchor=tk.W)
        self.tree.column('line', width=50, anchor=tk.CENTER)
        self.tree.column('content', width=450, anchor=tk.W)

        # スクロールバー
        self.vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # レイアウト
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.vsb.grid(row=0, column=1, sticky='ns')
        self.hsb.grid(row=1, column=0, sticky='ew')

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # イベントバインド
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._show_context_menu)

    def clear(self) -> None:
        """リストをクリアします。"""
        self._results.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def add_result(self, result: GrepResult) -> None:
        """単一の検索結果をリストに追加します。"""
        self._results.append(result)
        self.tree.insert(
            '',
            tk.END,
            values=(
                os.path.basename(result.file_path),
                result.line_number,
                result.line_content.strip(),
            ),
        )

    def get_selected_result(self) -> Optional[GrepResult]:
        """現在選択されている結果を返します。"""
        selected = self.tree.selection()
        if not selected:
            return None

        # インデックスを取得（ Treeview の順番と _results の順番が一致している前提）
        index = self.tree.index(selected[0])
        if 0 <= index < len(self._results):
            return self._results[index]
        return None

    def _on_double_click(self, event: tk.Event) -> None:
        """項目がダブルクリックされた時、ファイルを開きます。"""
        result = self.get_selected_result()
        if result and os.path.exists(result.file_path):
            try:
                os.startfile(result.file_path)
            except Exception as e:
                self.log_and_show_error(f'Failed to open file: {e}')

    def _show_context_menu(self, event: tk.Event) -> None:
        """右クリックメニューを表示します。"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label='Open File', command=self._open_file)
            menu.add_command(label='Open in Explorer', command=self._open_in_explorer)
            menu.post(event.x_root, event.y_root)

    def _open_file(self) -> None:
        """選択されているファイルを開きます。"""
        result = self.get_selected_result()
        if result and os.path.exists(result.file_path):
            os.startfile(result.file_path)

    def _open_in_explorer(self) -> None:
        """選択されているファイルの場所をエクスプローラで開きます。"""
        result = self.get_selected_result()
        if result and os.path.exists(result.file_path):
            subprocess.run(['explorer', '/select,', os.path.normpath(result.file_path)])
