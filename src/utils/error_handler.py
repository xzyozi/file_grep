from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# UI側でエラーを表示するためのコールバック（アダプターが登録する）
_ui_error_callback: Optional[Callable[[str, str], None]] = None


def register_ui_error_callback(callback: Callable[[str, str], None]) -> None:
    """GUIアダプターが、エラーをユーザーに通知するための関数を登録します。"""
    global _ui_error_callback
    _ui_error_callback = callback


def log_and_show_error(title: str, message: str, exc_info: bool = False) -> None:
    """
    エラーをログに記録し、登録されている場合はGUIで通知します。
    GUIへの直接的な依存（messageboxなど）はありません。
    """
    logger.error(f"{title}: {message}", exc_info=exc_info)
    
    if _ui_error_callback:
        _ui_error_callback(title, message)
    else:
        # GUIが未登録ならコンソールへフォールバック
        print(f"--- UI ERROR [{title}] ---\n{message}\n----------------------")
