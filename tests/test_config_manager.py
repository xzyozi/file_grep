import json

import pytest

from src.core.config.config_manager import ConfigManager, ExcludeConfig


def test_load_default_when_missing(tmp_path):
    config_path = tmp_path / "exclude_test.json"
    manager = ConfigManager(config_name=str(config_path))

    assert manager.config.exclude_dirs == []
    assert manager.config.exclude_exts == []
    assert not config_path.exists()


def test_save_and_reload_config(tmp_path):
    config_path = tmp_path / "exclude_test.json"
    manager = ConfigManager(config_name=str(config_path))
    manager.update(exclude_dirs=[".git", "node_modules"], exclude_exts=["py", ".log"])

    assert config_path.exists()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["exclude_dirs"] == [".git", "node_modules"]
    assert data["exclude_exts"] == [".py", ".log"]

    new_manager = ConfigManager(config_name=str(config_path))
    assert new_manager.config.exclude_dirs == [".git", "node_modules"]
    assert new_manager.config.exclude_exts == [".py", ".log"]


def test_normalize_extension_values(tmp_path):
    config_path = tmp_path / "exclude_test.json"
    manager = ConfigManager(config_name=str(config_path))
    manager.update(exclude_exts=["TXT", "md", ".Pdf"], save=False)

    assert manager.config.exclude_exts == [".txt", ".md", ".pdf"]
