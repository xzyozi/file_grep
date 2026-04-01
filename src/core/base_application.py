from __future__ import annotations

import os
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
    すべての定形サービスとパスの管理を行います。
    """

    def __init__(self, gui_adapter: Optional[GUIProtocol] = None) -> None:
        # プロジェクトルートの絶対パスを取得
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        # 1. イベント管理
        self.event_dispatcher = EventDispatcher()
        
        # 2. 設定管理 (デフォルトで settings.json)
        self.settings_manager = SettingsManager(self.event_dispatcher)
        
        # 3. 翻訳エンジンの初期化 (絶対パスを使用)
        locales_dir = os.path.join(self.root_dir, "locales")
        self.translator = Translator(self.settings_manager, locales_dir=locales_dir)
        
        # 4. GUIアダプター
        self.gui: Optional[GUIProtocol] = gui_adapter
        
        # 5. 検索エンジン (Mock / Real)
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
        self.gui = gui_adapter

    def run(self) -> None:
        if self.gui:
            self.gui.initialize()
            
            # 初期設定を反映させる（テーマ等）
            initial_theme = self.settings_manager.get_setting("theme", "light")
            if hasattr(self.gui, 'apply_theme'):
                 self.gui.apply_theme(initial_theme) # type: ignore
            
            self.gui.run()

    def quit(self) -> None:
        if self.gui:
            self.gui.quit()
        # 終了時に設定を強制保存
        self.settings_manager.save_settings()
