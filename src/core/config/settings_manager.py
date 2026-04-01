from __future__ import annotations

import json
import os
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from src.core.event_dispatcher import EventDispatcher

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    アプリケーションの設定管理クラス。
    JSONファイルへの保存・読み込みと、設定変更の通知を行います。
    """

    def __init__(self, event_dispatcher: EventDispatcher, config_path: str = "settings.json") -> None:
        self.event_dispatcher = event_dispatcher
        self.config_path = config_path
        self.settings: Dict[str, Any] = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """設定ファイルを読み込みます。存在しない場合はデフォルト(空)を返します。"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load settings: {e}")
        return {}

    def get_setting(self, key: str, default: Any = None) -> Any:
        """設定値を取得します。"""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any, save: bool = True) -> None:
        """設定値を更新し、イベントを通知します。"""
        if self.settings.get(key) != value:
            self.settings[key] = value
            self.event_dispatcher.dispatch("SETTINGS_CHANGED", self.settings)
            if save:
                self.save_settings()

    def save_settings(self) -> None:
        """現在の設定をファイルに書き出します。"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Settings saved successfully.")
        except OSError as e:
            logger.error(f"Failed to save settings: {e}")
