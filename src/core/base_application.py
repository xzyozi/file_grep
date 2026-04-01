from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Callable

from src.core.event_dispatcher import EventDispatcher
from src.core.config.settings_manager import SettingsManager
from src.utils.i18n import Translator

if TYPE_CHECKING:
    from src.core.gui_interface import GUIProtocol
    from src.grep.interface import GrepEngineProtocol


class BaseApplication:
    """
    アプリケーションのコア管理クラス。
    GUIフレームワークに依存せず、すべての基盤サービスを集約します。
    """

    def __init__(self, gui_adapter: Optional[GUIProtocol] = None) -> None:
        # 1. 基盤サービスの構築
        self.event_dispatcher = EventDispatcher()
        self.settings_manager = SettingsManager(self.event_dispatcher)
        
        # 2. 翻訳エンジンの初期化 (locales フォルダを指定)
        self.translator = Translator(self.settings_manager, locales_dir="locales")
        
        # 3. GUIアダプターの保持
        self.gui: Optional[GUIProtocol] = gui_adapter
        
        # 4. 検索エンジンの保持 (Mock / Real)
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
            # サーバーモードやCLIモードなどのHeadless実行
            pass

    def quit(self) -> None:
        """安全にアプリケーションを終了します。"""
        if self.gui:
            self.gui.quit()
        # 必要なら設定の最終保存など
