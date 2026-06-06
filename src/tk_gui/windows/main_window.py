from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any, Dict

from src.tk_gui.base.base_toplevel_gui import BaseToplevelGUI

logger = logging.getLogger(__name__)

from src.tk_gui.components.grep_result_list_component import GrepResultListComponent
from src.tk_gui.components.history_list_component import HistoryListComponent
from src.tk_gui.components.phrase_list_component import PhraseListComponent
from src.tk_gui.components.search_param_component import SearchParamComponent
from src.tk_gui.windows.settings_window import SettingsWindow

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication
    from src.grep.engine import GrepResult


class MainWindow(BaseToplevelGUI):
    """
    アプリケーションのメインウィンドウ。
    検索条件の入力と、複数のタブ、設定画面へのアクセスを提供します。
    """

    def __init__(self, master: tk.Misc, app_instance: BaseApplication) -> None:
        super().__init__(master, app_instance)
        self.title('Grep Engine - Advanced')
        self.geometry('1000x800')

        self.engine = self.app.engine

        # スレッドセーフな検索結果キューと検索状態
        self._result_queue = queue.Queue()
        self._is_searching = False
        self._poll_id = None

        # UI構築
        self._create_widgets()
        self._refresh_menu()

        # 設定/言語変更の購読
        self.app.event_dispatcher.subscribe('SETTINGS_CHANGED', self._on_settings_changed)
        self.app.event_dispatcher.subscribe('LANGUAGE_CHANGED', self._refresh_menu)

    def _refresh_menu(self) -> None:
        """メニューバーを生成（または再構築）します。言語変更時に呼び出されます。"""
        _t = self.app.translator
        menubar = tk.Menu(self)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=_t('exit'), command=self.app.quit)
        menubar.add_cascade(label=_t('file'), menu=file_menu)

        # Edit (Settings)
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label=_t('settings'), command=self._on_open_settings)
        menubar.add_cascade(label=_t('edit'), menu=edit_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label=_t('about'),
            command=lambda: messagebox.showinfo(_t('about'), 'Grep Engine v1.0\nModernized Search Tool')
        )
        menubar.add_cascade(label=_t('help'), menu=help_menu)

        self.config(menu=menubar)

    def _create_widgets(self) -> None:
        _t = self.app.translator
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
        self.notebook.add(self.result_list, text=_t('search_results'))

        # 2. 履歴タブ
        self.history_list = HistoryListComponent(self.notebook, self.app, on_select=self._apply_history)
        self.notebook.add(self.history_list, text=_t('search_history'))

        # 3. スニペット（定型文）タブ
        self.phrase_list = PhraseListComponent(
            self.notebook,
            self.app,
            on_select=lambda label, pattern, is_regex: self.search_params.set_values(keyword=pattern, regex_mode=is_regex)
        )
        self.notebook.add(self.phrase_list, text=_t('snippets'))

    def _on_settings_changed(self, settings: Dict[str, Any]) -> None:
        """設定が変更された際の処理（テーマの適用など）。"""
        theme_name = settings.get('theme', 'light')
        if self.app.gui and hasattr(self.app.gui, 'apply_theme'):
             self.app.gui.apply_theme(theme_name)

    def _on_open_settings(self) -> None:
        SettingsWindow(self, self.app, self.app.settings_manager)

    def _apply_history(self, keyword: str, directory: str, is_regex: bool) -> None:
        self.search_params.set_values(keyword=keyword, directory=directory, regex_mode=is_regex)
        self.notebook.select(0)

    def _on_start_search(self, target_dir: str, search_text: str, regex_mode: bool, ignore_case: bool, whole_word: bool, exclude_dirs: list[str], exclude_file_patterns: list[str]) -> None:
        """検索開始処理。"""
        engine = self.engine
        if not engine:
            messagebox.showerror('Error', 'GrepEngine is not loaded.')
            return

        # SettingsManager から除外拡張子リストを取得してパース
        raw_exts = ""
        try:
            raw_exts = self.app.settings_manager.get_setting("exclude_extensions")
        except Exception:
            raw_exts = ""
        exclude_exts = [e.strip() for e in raw_exts.split(',') if e.strip()]
        # 拡張子がドットで始まらない場合は補正
        exclude_exts = [('.' + e) if not e.startswith('.') else e for e in exclude_exts]

        self.history_list.add_history(search_text, target_dir, regex_mode)
        self.notebook.select(0)
        self.result_list.clear()
        self.progress_var.set(0)
        self.status_var.set('Searching...')
        self.search_params.set_searching_state(True)

        # 検索状態のリセットとポーリング開始
        self._is_searching = True
        self._result_queue = queue.Queue()
        self._poll_results()

        t = threading.Thread(
            target=lambda: engine.search(
                target_dir=target_dir,
                search_text=search_text,
                regex_mode=regex_mode,
                ignore_case=ignore_case,
                whole_word=whole_word,
                exclude_dirs=exclude_dirs,
                exclude_exts=exclude_exts,
                exclude_file_patterns=exclude_file_patterns,
                on_progress=self._update_progress,
                on_result=self._add_to_list,
                on_complete=self._search_complete,
                on_error=lambda msg, e: logger.warning(f"{msg}: {e}"),
            ),
            daemon=True
        )
        t.start()

    def _on_stop_search(self) -> None:
        """検索停止処理。"""
        engine = self.engine
        if engine:
            engine.stop()
            self.status_var.set('Stopping...')
        
        # 停止したら即座にポーリング停止と残存フラッシュを行い状態を更新
        self._is_searching = False
        if self._poll_id:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self._flush_remaining_results()
        self.search_params.set_searching_state(False)

    def _poll_results(self) -> None:
        """定期的にキューから検索結果を取り出し、一括でリストに追加します。"""
        if not self._is_searching:
            return

        max_batch = 500
        results = []
        for _ in range(max_batch):
            try:
                result = self._result_queue.get_nowait()
                results.append(result)
            except queue.Empty:
                break

        if results:
            self.result_list.add_results(results)

        # 100ms 間隔で再スケジュール
        self._poll_id = self.after(100, self._poll_results)

    def _flush_remaining_results(self) -> None:
        """キューに残っている検索結果をすべてUIに追加します。"""
        results = []
        while True:
            try:
                results.append(self._result_queue.get_nowait())
            except queue.Empty:
                break
        if results:
            self.result_list.add_results(results)

    def _update_progress(self, current: int, total: int) -> None:
        if not self._is_searching:
            return
        percent = (current / total) * 100 if total > 0 else 0
        self.after(0, lambda: self.progress_var.set(percent))
        self.after(0, lambda: self.status_var.set(f'Searching: {current} / {total} files'))

    def _add_to_list(self, result: GrepResult) -> None:
        """検索スレッドから呼び出されます。結果をキューに追加するのみです。"""
        if self._is_searching:
            self._result_queue.put(result)

    def _search_complete(self, hit_count: int) -> None:
        def _gui_complete():
            self._is_searching = False
            if self._poll_id:
                self.after_cancel(self._poll_id)
                self._poll_id = None
            self._flush_remaining_results()
            self.status_var.set(f'Complete! hits: {hit_count}')
            self.search_params.set_searching_state(False)
            self.progress_var.set(100)

        self.after(0, _gui_complete)
