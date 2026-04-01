from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Any

from src.core.config.defaults import THEMES
from src.utils.error_handler import log_and_show_error

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication


class BaseFrameGUI(tk.Frame):
    """
    Tkinter の Frame コンポーネントの基底クラス。
    """

    def __init__(
        self, master: tk.Misc, app_instance: BaseApplication, **kwargs: Any
    ) -> None:
        super().__init__(master, **kwargs)
        self.master = master
        self.app = app_instance
        self.log_and_show_error = log_and_show_error

        # GUIアダプター経由でテーマを適用 (任意)
        # 通常は親ウィンドウが widget_tree 全体に適用するが、
        # 動的に生成されるフレームなどは念のため。
        gui_adapter: Any = self.app.gui
        if hasattr(gui_adapter, 'theme_manager') and gui_adapter.theme_manager:
            theme_name = gui_adapter.theme_manager.get_current_theme()
            gui_adapter.theme_manager.apply_theme_to_widget_tree(self, THEMES[theme_name])

    def _create_common_widgets(self) -> None:
        pass
