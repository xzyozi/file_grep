from __future__ import annotations

from typing import Any, Callable, Dict, List


class EventDispatcher:
    """
    アプリケーション全体でイベントをやり取りするためのディスパッチャ。
    Publish/Subscribe パターンを実装します。
    """

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[..., Any]]] = {}

    def subscribe(self, event_type: str, listener: Callable[..., Any]) -> None:
        """イベントにリスナーを登録します。"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def dispatch(self, event_type: str, *args: Any, **kwargs: Any) -> None:
        """指定したイベントを発火し、登録されているリスナーに通知します。"""
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                try:
                    listener(*args, **kwargs)
                except Exception as e:
                    print(f"Error in listener for event {event_type}: {e}")

    def unsubscribe(self, event_type: str, listener: Callable[..., Any]) -> None:
        """登録済みのリスナーを削除します。"""
        if event_type in self._listeners:
            self._listeners[event_type].remove(listener)
