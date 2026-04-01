from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import TYPE_CHECKING, Optional

from src.tk_gui.windows.main_window import MainWindow
from src.tk_gui.theme_manager import ThemeManager
from src.utils.error_handler import register_ui_error_callback

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class TkinterGUIAdapter:
    """
    Tkinterフレームワーク特有のロジックを管理するアダプタークラス。
    GUIProtocol を満たし、UI とアプリ基盤 (Core) を繋ぎます。
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
        self.theme_manager.apply_theme('light')

        # 疎結合なエラーハンドラーの接続 (DI)
        # log_and_show_error を呼び出した際、Tkinter のメッセージボックスが表示されるようにする。
        register_ui_error_callback(self.show_error)

        # メインウィンドウを生成し、アプリ基盤を渡す
        self.main_window = MainWindow(self.root, self.app)
        
        # 終了イベントのハンドリング
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
        """インフォ形式のメッセージを表示します。"""
        messagebox.showinfo(title, message)

    def show_error(self, title: str, message: str) -> None:
        """エラー形式のメッセージを表示します。"""
        messagebox.showerror(title, message)

    def quit(self) -> None:
        """アプリケーションを安全に終了します。"""
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None
            self.main_window = None
            self.theme_manager = None
