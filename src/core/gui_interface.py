from __future__ import annotations

from typing import Protocol, Any


class GUIProtocol(Protocol):
    """
    GUIフレームワークに依存しない、UI側の共通インターフェースです。
    """

    def initialize(self) -> None:
        """GUIの初期設定（ウィンドウ生成など）を行います。"""
        ...

    def run(self) -> None:
        """GUIのメインループを開始します。"""
        ...

    def show_message(self, title: str, message: str) -> None:
        """ユーザーにメッセージを表示します。"""
        ...

    def show_error(self, title: str, message: str) -> None:
        """ユーザーにエラーを表示します。"""
        ...

    def quit(self) -> None:
        """GUIを終了します。"""
        ...
