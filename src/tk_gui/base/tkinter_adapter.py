from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import TYPE_CHECKING, Optional

from src.tk_gui.theme_manager import ThemeManager
from src.tk_gui.windows.main_window import MainWindow
from src.utils.error_handler import register_ui_error_callback

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class TkinterGUIAdapter:
    """
    Tkinterフレームワーク特有のロジックを管理するアダプタークラス。
    """

    def __init__(self, app_instance: BaseApplication) -> None:
        self.app = app_instance
        self.root: Optional[tk.Tk] = None
        self.main_window: Optional[MainWindow] = None
        self.theme_manager: Optional[ThemeManager] = None

    def initialize(self) -> None:
        """Tkinter のルートウィンドウを初期化し、サービスを UI と接続します。"""
        self.root = tk.Tk()
        self.root.withdraw()

        # テーマ管理の開始
        self.theme_manager = ThemeManager(self.root)

        # 修正: 保存されている設定値を読み込み、起動時のテーマを決定する
        initial_theme = self.app.settings_manager.get_setting("theme", "light")
        self.theme_manager.apply_theme(initial_theme)

        # 疎結合なエラーハンドラーの接続
        register_ui_error_callback(self.show_error)

        # メインウィンドウを生成
        self.main_window = MainWindow(self.root, self.app)
        self.main_window.protocol('WM_DELETE_WINDOW', self.quit)
        self.main_window.deiconify()

    def run(self) -> None:
        """Tkinter のメインループを開始します。"""
        if self.root:
            self.root.mainloop()

    def apply_theme(self, theme_name: str) -> None:
        """テーマを適用します。"""
        if self.theme_manager:
            self.theme_manager.apply_theme(theme_name)

    def show_message(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def quit(self) -> None:
        """アプリケーションを終了し、設定を保存。"""
        # アプリ基盤側に設定の最終保存を依頼
        self.app.settings_manager.save_settings()

        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None
            self.main_window = None
            self.theme_manager = None
