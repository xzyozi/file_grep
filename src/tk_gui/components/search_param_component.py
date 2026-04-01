from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import TYPE_CHECKING, Callable

from src.tk_gui.base.base_frame_gui import BaseFrameGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class SearchParamComponent(BaseFrameGUI):
    """
    検索条件（ディレクトリ、キーワード、オプション）を入力し、
    検索実行を制御するコンポーネント。
    """

    def __init__(
        self,
        master: tk.Misc,
        app_instance: BaseApplication,
        on_start: Callable[[str, str, bool], None],
        on_stop: Callable[[], None],
    ) -> None:
        super().__init__(master, app_instance)
        self.on_start = on_start
        self.on_stop = on_stop

        self._create_widgets()

    def _create_widgets(self) -> None:
        # パラメータ入力エリア
        input_frame = ttk.LabelFrame(self, text='Search Configuration', padding=(10, 5))
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        # 1行目: ディレクトリ選択
        ttk.Label(input_frame, text='Directory:').grid(row=0, column=0, sticky=tk.W)
        self.dir_var = tk.StringVar(value=os.getcwd())
        self.dir_entry = ttk.Entry(input_frame, textvariable=self.dir_var, width=50)
        self.dir_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text='Browse...', command=self._on_browse).grid(
            row=0, column=2, padx=2
        )

        # 2行目: 検索キーワード & 正規表現
        ttk.Label(input_frame, text='Keyword:').grid(row=1, column=0, sticky=tk.W)
        self.keyword_var = tk.StringVar(value='')
        self.keyword_entry = ttk.Entry(input_frame, textvariable=self.keyword_var, width=50)
        self.keyword_entry.grid(row=1, column=1, padx=5, pady=5)

        self.regex_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(input_frame, text='Use Regex', variable=self.regex_var).grid(
            row=1, column=2, sticky=tk.W
        )

        # 3行目: アクションボタン
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=1, pady=10)

        self.start_btn = ttk.Button(
            btn_frame, text='Search Engine Start!', command=self._handle_start
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            btn_frame, text='Stop', state=tk.DISABLED, command=self._handle_stop
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

    def _on_browse(self) -> None:
        path = filedialog.askdirectory(initialdir=self.dir_var.get())
        if path:
            self.dir_var.set(path)

    def _handle_start(self) -> None:
        target_dir = self.dir_var.get()
        search_text = self.keyword_var.get()
        regex_mode = self.regex_var.get()
        self.on_start(target_dir, search_text, regex_mode)

    def _handle_stop(self) -> None:
        self.on_stop()

    def set_searching_state(self, is_searching: bool) -> None:
        """検索中かどうかに応じてボタンの有効化/無効化を切り替えます。"""
        if is_searching:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def set_values(self, keyword: Optional[str] = None, directory: Optional[str] = None, regex_mode: Optional[bool] = None) -> None:
        """入力欄の値を設定します。"""
        if keyword is not None:
            self.keyword_var.set(keyword)
        if directory is not None:
            self.dir_var.set(directory)
        if regex_mode is not None:
            self.regex_var.set(regex_mode)
