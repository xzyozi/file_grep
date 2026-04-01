from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from src.core.event_dispatcher import EventDispatcher

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    アプリケーションの設定管理クラス。
    常にプロジェクトルートを基準とした絶対パスでファイルを読み書きします。
    """

    def __init__(self, event_dispatcher: EventDispatcher, config_name: str = "settings.json") -> None:
        self.event_dispatcher = event_dispatcher

        # プロジェクトルート (src の一階層上) を基準に絶対パスを構築
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.config_path = os.path.join(root_dir, config_name)

        logger.info(f"Target config path: {self.config_path}")
        self.settings: Dict[str, Any] = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """設定ファイルを読み込みます。"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Settings loaded from {self.config_path}")
                    return data
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load settings from {self.config_path}: {e}")
        else:
            logger.info(f"No settings file found at {self.config_path}, using defaults.")
        return {}

    def get_setting(self, key: str, default: Any = None) -> Any:
        """設定項目を取得します。"""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any, save: bool = True) -> None:
        """設定値を更新し、永続化します。"""
        # 値に変更がある場合のみ書き出し
        if self.settings.get(key) != value:
            self.settings[key] = value
            # 全コンポーネントに変更を通知
            self.event_dispatcher.dispatch("SETTINGS_CHANGED", self.settings)
            if save:
                self.save_settings()

    def save_settings(self) -> None:
        """現在の設定を JSON 形式で保存します。"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
            logger.info(f"Settings explicitly saved to {self.config_path}")
        except OSError as e:
            logger.error(f"Failed to save settings: {e}")
