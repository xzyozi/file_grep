from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Any

from src.core.config.defaults import THEMES

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class BaseToplevelGUI(tk.Toplevel):
    """
    Tkinter の Toplevel ウィンドウの基底クラス。
    アプリケーションサービスへのアクセスとテーマの自動適用を提供します。
    """

    def __init__(
        self, master: tk.Misc, app_instance: BaseApplication, **kwargs: Any
    ) -> None:
        super().__init__(master, **kwargs)
        self.master = master
        self.app = app_instance

        # GUIアダプター (TkinterGUIAdapter) 経由でテーマを適用
        gui_adapter: Any = self.app.gui
        if hasattr(gui_adapter, 'theme_manager') and gui_adapter.theme_manager:
            theme_name = gui_adapter.theme_manager.get_current_theme()
            gui_adapter.theme_manager.apply_theme_to_widget_tree(self, THEMES[theme_name])

    def _create_common_widgets(self) -> None:
        pass
