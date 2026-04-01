from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Callable

from src.core.event_dispatcher import EventDispatcher

if TYPE_CHECKING:
    from src.core.gui_interface import GUIProtocol
    from src.grep.interface import GrepEngineProtocol


class BaseApplication:
    """
    アプリケーションのコア管理クラス。
    GUI（tkinterなど）には依存せず、設定、イベント、検索エンジンなどの
    サービスを集約して管理します。
    """

    def __init__(self, gui_adapter: Optional[GUIProtocol] = None) -> None:
        # イベント管理
        self.event_dispatcher = EventDispatcher()
        
        # 設定管理（将来的に SettingsManager に置き換え）
        self.settings: Dict[str, Any] = {}
        
        # 翻訳機能
        self.translator: Callable[[str], str] = lambda x: x
        
        # GUIアダプター（Tkinter, wxPython, CLIなど）
        self.gui: Optional[GUIProtocol] = gui_adapter
        
        # 検索エンジンを保持
        self.engine: Optional[GrepEngineProtocol] = self._init_engine()

    def _init_engine(self) -> Optional[GrepEngineProtocol]:
        """検索エンジンを初期化します。"""
        try:
            from src.grep.engine import GrepEngine
            return GrepEngine()
        except (ImportError, Exception):
            try:
                from src.grep.mock_engine import MockGrepEngine
                return MockGrepEngine()
            except ImportError:
                return None

    def set_gui(self, gui_adapter: GUIProtocol) -> None:
        """後からGUIアダプターをセットします。"""
        self.gui = gui_adapter

    def run(self) -> None:
        """
        アプリケーションを起動します。
        具体的なウィンドウの生成やループ開始は GUI アダプターに委譲します。
        """
        if self.gui:
            self.gui.initialize()
            self.gui.run()
        else:
            print("Running in Headless Mode (CLI or other)")
            # CLI用のロジック等をここに記述

    def quit(self) -> None:
        """アプリケーションをクリーンアップして終了します。"""
        if self.gui:
            self.gui.quit()
        # ここにエンジンの停止、設定の保存などを記述
