from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any, Dict

from src.tk_gui.base.base_toplevel_gui import BaseToplevelGUI
from src.tk_gui.components.grep_result_list_component import GrepResultListComponent
from src.tk_gui.components.history_list_component import HistoryListComponent
from src.tk_gui.components.phrase_list_component import PhraseListComponent
from src.tk_gui.components.search_param_component import SearchParamComponent

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication
    from src.grep.engine import GrepResult


class MainWindow(BaseToplevelGUI):
    """
    アプリケーションのメインウィンドウ。
    検索条件の入力と、複数のタブ（結果、履歴、スニペット）を管理します。
    """

    def __init__(self, master: tk.Misc, app_instance: BaseApplication) -> None:
        super().__init__(master, app_instance)
        self.title('Grep Engine - Advanced')
        self.geometry('1000x800')

        # 検索エンジンの準備
        self.engine = self._load_engine()
        self._create_widgets()

    def _load_engine(self):
        """エンジンをロードします。"""
        try:
            from src.grep.engine import GrepEngine
            return GrepEngine()
        except (ImportError, Exception):
            try:
                from src.grep.mock_engine import MockGrepEngine
                return MockGrepEngine()
            except ImportError:
                return None

    def _create_widgets(self) -> None:
        # 上部: 全タブ共通の検索設定エリア
        self.search_params = SearchParamComponent(
            self,
            self.app,
            on_start=self._on_start_search,
            on_stop=self._on_stop_search
        )
        self.search_params.pack(fill=tk.X, padx=10, pady=5)

        # 中部: 進捗表示
        progress_frame = ttk.Frame(self, padding=(10, 0))
        progress_frame.pack(fill=tk.X)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(5, 2))

        self.status_var = tk.StringVar(value='Ready')
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)

        # 下部: タブインターフェース
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. 結果リストタブ
        self.result_list = GrepResultListComponent(self.notebook, self.app)
        self.notebook.add(self.result_list, text='Search Results')

        # 2. 履歴タブ
        self.history_list = HistoryListComponent(self.notebook, self.app, on_select=self._apply_history)
        self.notebook.add(self.history_list, text='Search History')

        # 3. スニペット（定型文）タブ
        self.phrase_list = PhraseListComponent(self.notebook, self.app, on_select=self._apply_snippet)
        self.notebook.add(self.phrase_list, text='Snippets / Patterns')

    def _apply_history(self, keyword: str, directory: str, is_regex: bool) -> None:
        """履歴から検索条件を復元し、結果タブに切り替えます。"""
        self.search_params.set_values(keyword=keyword, directory=directory, regex_mode=is_regex)
        self.notebook.select(0)
        self.status_var.set('History conditions applied.')

    def _apply_snippet(self, pattern: str) -> None:
        """スニペットからパターンをセットし、正規表現モードをONにして結果タブに切り替えます。"""
        self.search_params.set_values(keyword=pattern, regex_mode=True)
        self.notebook.select(0)
        self.status_var.set('Snippet pattern applied.')

    def _on_start_search(self, target_dir: str, search_text: str, regex_mode: bool) -> None:
        """検索開始。"""
        if not self.engine:
            messagebox.showerror('Error', 'GrepEngine is not loaded.')
            return

        if not os.path.isdir(target_dir):
            messagebox.showwarning('Warning', 'Target directory does not exist.')
            return
        
        if not search_text:
            messagebox.showwarning('Warning', 'Please enter a search keyword.')
            return

        # 履歴に追加
        self.history_list.add_history(search_text, target_dir, regex_mode)
        
        # UI状態を検索中に変更 & 結果タブへスイッチ
        self.notebook.select(0)
        self.result_list.clear()
        self.progress_var.set(0)
        self.status_var.set('Searching...')
        self.search_params.set_searching_state(True)

        t = threading.Thread(
            target=lambda: self.engine.search(
                target_dir=target_dir,
                search_text=search_text,
                regex_mode=regex_mode,
                on_progress=self._update_progress,
                on_result=self._add_to_list,
                on_complete=self._search_complete,
            ),
            daemon=True
        )
        t.start()

    def _on_stop_search(self) -> None:
        """検索中止。"""
        if self.engine:
            self.engine.stop()
            self.status_var.set('Stopping...')

    def _update_progress(self, current: int, total: int) -> None:
        """スレッドセーフな進捗更新。"""
        percent = (current / total) * 100 if total > 0 else 0
        self.after(0, lambda: self.progress_var.set(percent))
        self.after(0, lambda: self.status_var.set(f'Scanning: {current} / {total} files'))

    def _add_to_list(self, result: GrepResult) -> None:
        """スレッドセーフな結果追加。"""
        self.after(0, lambda: self.result_list.add_result(result))

    def _search_complete(self, hit_count: int) -> None:
        """スレッドセーフな完了処理。"""
        self.after(0, lambda: self.status_var.set(f'Complete! Total hits: {hit_count}'))
        self.after(0, lambda: self.search_params.set_searching_state(False))
