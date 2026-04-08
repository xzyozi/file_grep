from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import TYPE_CHECKING, Callable, Optional

from src.tk_gui.base.base_frame_gui import BaseFrameGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class SearchParamComponent(BaseFrameGUI):
    """
    検索条件（ディレクトリ、キーワード、正規表現モード）を管理するコンポーネント。
    """

    def __init__(
        self,
        master: tk.Misc,
        app_instance: BaseApplication,
        on_start: Callable[[str, str, bool, bool, bool, list[str]], None],
        on_stop: Callable[[], None]
    ) -> None:
        super().__init__(master, app_instance)
        self.on_start = on_start
        self.on_stop = on_stop

        # 入力値の保持用
        self.dir_var = tk.StringVar(value=os.getcwd())
        self.keyword_var = tk.StringVar()
        self.regex_var = tk.BooleanVar(value=False)
        self.ignore_case_var = tk.BooleanVar(value=False)
        self.whole_word_var = tk.BooleanVar(value=False)
        # デフォルトで除外するディレクトリ
        self.exclude_dirs_var = tk.StringVar(value=".git,node_modules,__pycache__")
        self.show_advanced = False

        self._create_widgets()

        # 言語変更イベントの購読
        self.app.event_dispatcher.subscribe('LANGUAGE_CHANGED', self._refresh_labels)

    def _create_widgets(self) -> None:
        # ディレクトリ選択
        self.dir_label = ttk.Label(self)
        self.dir_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        self.dir_entry = ttk.Entry(self, textvariable=self.dir_var, width=60)
        self.dir_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        self.browse_btn = ttk.Button(self, text="...", width=3, command=self._browse_directory)
        self.browse_btn.grid(row=0, column=2, sticky=tk.W, padx=2)

        # キーワード入力
        self.kw_label = ttk.Label(self)
        self.kw_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)

        self.kw_entry = ttk.Entry(self, textvariable=self.keyword_var, width=60)
        self.kw_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        self.kw_entry.bind('<Return>', lambda e: self._on_start_btn_click())

        # オプションと実行ボタン
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=1, sticky=tk.W, pady=5)

        self.regex_check = ttk.Checkbutton(btn_frame, variable=self.regex_var)
        self.regex_check.pack(side=tk.LEFT, padx=5)

        self.ignore_case_check = ttk.Checkbutton(btn_frame, variable=self.ignore_case_var)
        self.ignore_case_check.pack(side=tk.LEFT, padx=5)

        self.whole_word_check = ttk.Checkbutton(btn_frame, variable=self.whole_word_var)
        self.whole_word_check.pack(side=tk.LEFT, padx=5)

        self.start_btn = ttk.Button(btn_frame, command=self._on_start_btn_click)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.advanced_btn = ttk.Button(btn_frame, command=self._toggle_advanced)
        self.advanced_btn.pack(side=tk.LEFT, padx=5)

        # 詳細設定エリア (初期状態は非表示)
        self.advanced_frame = ttk.Frame(self)
        # grid配置はトグル時に行うためここでは定義のみ

        self.ex_dir_label = ttk.Label(self.advanced_frame)
        self.ex_dir_label.pack(side=tk.LEFT, padx=5)

        self.ex_dir_entry = ttk.Entry(self.advanced_frame, textvariable=self.exclude_dirs_var, width=50)
        self.ex_dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.ex_dir_hint_label = ttk.Label(self.advanced_frame, font=("", 8), foreground="gray")
        self.ex_dir_hint_label.pack(side=tk.LEFT, padx=5)

        self.grid_columnconfigure(1, weight=1)

        # 初期ラベル設定
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        """多言語設定に従ってラベルテキストを更新します。"""
        _t = self.app.translator
        self.dir_label.config(text=_t('directory') + ":")
        self.kw_label.config(text=_t('keyword') + ":")
        self.regex_check.config(text=_t('regex'))
        self.ignore_case_check.config(text=_t('ignore_case'))
        self.whole_word_check.config(text=_t('whole_word'))
        self.start_btn.config(text=_t('start'))
        self.stop_btn.config(text=_t('stop'))
        self.advanced_btn.config(text=_t('advanced'))
        self.ex_dir_label.config(text=_t('exclude_dirs') + ":")
        self.ex_dir_hint_label.config(text=_t('exclude_dirs_hint'))

    def _browse_directory(self) -> None:
        path = filedialog.askdirectory(initialdir=self.dir_var.get())
        if path:
            self.dir_var.set(path)

    def _on_start_btn_click(self) -> None:
        # カンマ区切りの文字列をリストに変換 (空文字は除外)
        exclude_dirs = [d.strip() for d in self.exclude_dirs_var.get().split(',') if d.strip()]
        
        self.on_start(
            self.dir_var.get(),
            self.keyword_var.get(),
            self.regex_var.get(),
            self.ignore_case_var.get(),
            self.whole_word_var.get(),
            exclude_dirs
        )

    def _toggle_advanced(self) -> None:
        """詳細設定エリアの表示/非表示を切り替えます。"""
        self.show_advanced = not self.show_advanced
        if self.show_advanced:
            self.advanced_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        else:
            self.advanced_frame.grid_forget()

    def set_searching_state(self, is_searching: bool) -> None:
        """検索中かどうかに応じてボタンの有効化/無効化を切り替えます。"""
        if is_searching:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def set_values(
        self,
        keyword: Optional[str] = None,
        directory: Optional[str] = None,
        regex_mode: Optional[bool] = None,
        ignore_case: Optional[bool] = None,
        whole_word: Optional[bool] = None,
        exclude_dirs: Optional[list[str]] = None
    ) -> None:
        """入力欄の値を設定します。"""
        if keyword is not None:
            self.keyword_var.set(keyword)
        if directory is not None:
            self.dir_var.set(directory)
        if regex_mode is not None:
            self.regex_var.set(regex_mode)
        if ignore_case is not None:
            self.ignore_case_var.set(ignore_case)
        if whole_word is not None:
            self.whole_word_var.set(whole_word)
        if exclude_dirs is not None:
            self.exclude_dirs_var.set(",".join(exclude_dirs))
