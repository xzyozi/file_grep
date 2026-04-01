from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, Optional, Callable

from src.core.event_dispatcher import EventDispatcher
from src.core.config.settings_manager import SettingsManager
from src.core.config.history_manager import HistoryManager
from src.utils.i18n import Translator

if TYPE_CHECKING:
    from src.core.gui_interface import GUIProtocol
    from src.grep.interface import GrepEngineProtocol


class BaseApplication:
    """
    アプリケーションのコア管理クラス。
    各サービス（設定、履歴、翻訳、エンジン）を集約します。
    """

    def __init__(self, gui_adapter: Optional[GUIProtocol] = None) -> None:
        # プロジェクトルートの絶対パスを取得
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        # 1. サービス構築
        self.event_dispatcher = EventDispatcher()
        self.settings_manager = SettingsManager(self.event_dispatcher)
        self.history_manager = HistoryManager()
        
        # 2. 翻訳エンジンの初期化
        locales_dir = os.path.join(self.root_dir, "locales")
        self.translator = Translator(self.settings_manager, locales_dir=locales_dir)
        
        # 3. GUI
        self.gui: Optional[GUIProtocol] = gui_adapter
        
        # 4. エンジン
        self.engine: Optional[GrepEngineProtocol] = self._init_engine()

    def _init_engine(self) -> Optional[GrepEngineProtocol]:
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
        self.gui = gui_adapter

    def run(self) -> None:
        if self.gui:
            self.gui.initialize()
            initial_theme = self.settings_manager.get_setting("theme", "light")
            if hasattr(self.gui, 'apply_theme'):
                 self.gui.apply_theme(initial_theme)
            self.gui.run()

    def quit(self) -> None:
        if self.gui:
            self.gui.quit()
        self.settings_manager.save_settings()
        self.history_manager.save_history() # 履歴も終了時に保存
