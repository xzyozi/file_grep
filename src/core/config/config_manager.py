from __future__ import annotations

from dataclasses import asdict, dataclass, field
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.config.file_store import read_json, write_json

logger = logging.getLogger(__name__)

DEFAULT_EXCLUDE_CONFIG_PATH = "config/exclude.json"


@dataclass
class ExcludeConfig:
    exclude_dirs: List[str] = field(default_factory=list)
    exclude_exts: List[str] = field(default_factory=list)


class ConfigManager:
    """除外設定ファイルの読み込み・保存を担当するクラス。"""

    def __init__(self, config_name: str = DEFAULT_EXCLUDE_CONFIG_PATH) -> None:
        root_dir = Path(__file__).resolve().parents[3]
        self.config_path = root_dir / config_name
        self.config = self.load()

    def load(self) -> ExcludeConfig:
        """設定ファイルを読み込み、正しい形式へ正規化します。"""
        raw_data = read_json(str(self.config_path))
        if raw_data is None:
            logger.info(f"No exclude config found at {self.config_path}, using defaults.")
            raw_data = {}

        return self._normalize(raw_data)

    def save(self, config: Optional[ExcludeConfig] = None) -> None:
        """設定ファイルを保存します。"""
        if config is None:
            config = self.config

        write_json(str(self.config_path), asdict(config))
        self.config = config
        logger.info(f"Exclude settings saved to {self.config_path}")

    def update(
        self,
        exclude_dirs: Optional[List[str]] = None,
        exclude_exts: Optional[List[str]] = None,
        save: bool = True
    ) -> ExcludeConfig:
        """現在の設定を更新し、必要に応じて保存します。"""
        if exclude_dirs is not None:
            self.config.exclude_dirs = self._normalize_list(exclude_dirs)
        if exclude_exts is not None:
            self.config.exclude_exts = self._normalize_extensions(exclude_exts)

        if save:
            self.save()

        return self.config

    def _normalize(self, data: Any) -> ExcludeConfig:
        if not isinstance(data, Dict):
            logger.warning("Exclude config data is not a dictionary. Falling back to defaults.")
            data = {}

        return ExcludeConfig(
            exclude_dirs=self._normalize_list(data.get("exclude_dirs", [])),
            exclude_exts=self._normalize_extensions(data.get("exclude_exts", []))
        )

    def _normalize_list(self, value: Any) -> List[str]:
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []

        return [str(item).strip() for item in value if str(item).strip()]

    def _normalize_extensions(self, value: Any) -> List[str]:
        exts = self._normalize_list(value)
        normalized: List[str] = []
        for ext in exts:
            if not ext.startswith("."):
                ext = f".{ext}"
            normalized.append(ext.lower())
        return normalized
