from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from src.tk_gui.base.base_toplevel_gui import BaseToplevelGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication
    from src.core.config.settings_manager import SettingsManager


class SettingsWindow(BaseToplevelGUI):
    """
    アプリケーションの設定（テーマ、言語など）を行うウィンドウ。
    """

    def __init__(
        self,
        master: tk.Misc,
        app_instance: BaseApplication,
        settings_manager: SettingsManager,
    ) -> None:
        super().__init__(master, app_instance)

        _t = self.app.translator
        self.title(_t('settings'))
        self.geometry('500x400')
        self.settings_manager = settings_manager

        # 値の保持用
        self.theme_var = tk.StringVar(value=self.settings_manager.get_setting("theme"))
        self.language_var = tk.StringVar(value=self.settings_manager.get_setting("language"))
        self.exclude_extensions_var = tk.StringVar(value=self.settings_manager.get_setting("exclude_extensions"))

        self._create_widgets()

    def _create_widgets(self) -> None:
        _t = self.app.translator

        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        # 外観設定
        appearance_frame = ttk.LabelFrame(container, text=_t('theme'), padding=10)
        appearance_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(appearance_frame, text=_t('theme') + ":").grid(row=0, column=0, sticky=tk.W, padx=5)
        theme_combo = ttk.Combobox(
            appearance_frame,
            textvariable=self.theme_var,
            values=['light', 'dark'],
            state='readonly'
        )
        theme_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)
        theme_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_settings(save=False))

        # 言語設定
        lang_frame = ttk.LabelFrame(container, text=_t('language'), padding=10)
        lang_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(lang_frame, text=_t('language') + ":").grid(row=0, column=0, sticky=tk.W, padx=5)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, values=['en', 'ja'], state='readonly')
        lang_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)

        # 除外拡張子設定
        ext_frame = ttk.LabelFrame(container, text=_t('exclude_extensions'), padding=10)
        ext_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(ext_frame, text=_t('exclude_extensions') + ":").grid(row=0, column=0, sticky=tk.W, padx=5)
        ext_entry = ttk.Entry(ext_frame, textvariable=self.exclude_extensions_var, width=40)
        ext_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)

        hint_label = ttk.Label(ext_frame, text=_t('exclude_extensions_hint'), font=("TkDefaultFont", 8), foreground="gray")
        hint_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(5, 0))

        # 下部ボタン
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        save_btn = ttk.Button(btn_frame, text="Save", command=self._on_save)
        save_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def _apply_settings(self, save: bool = False) -> None:
        """現在の入力を設定マネージャーに反映します。"""
        self.settings_manager.set_setting("theme", self.theme_var.get(), save=save)
        self.settings_manager.set_setting("language", self.language_var.get(), save=save)
        self.settings_manager.set_setting("exclude_extensions", self.exclude_extensions_var.get(), save=save)

    def _on_save(self) -> None:
        """設定を保存して閉じます。"""
        self._apply_settings(save=True)
        messagebox.showinfo("Success", "Settings saved successfully.")
        self.destroy()
