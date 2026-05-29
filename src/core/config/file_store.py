from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def read_json(path: str) -> Any:
    """指定パスから JSON ファイルを読み込みます。"""
    file_path = Path(path)
    if not file_path.exists():
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Failed to read JSON from {path}: {e}")
        return None


def write_json(path: str, data: Any) -> None:
    """指定パスへ JSON ファイルを書き込みます。"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except OSError as e:
        logger.error(f"Failed to write JSON to {path}: {e}")
