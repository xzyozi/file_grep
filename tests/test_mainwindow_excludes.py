import os
import time

import pytest
import tkinter as tk

from src.core.base_application import BaseApplication
from src.tk_gui.windows.main_window import MainWindow


if not os.environ.get("DISPLAY"):
    pytest.skip("Skipping UI tests because no DISPLAY is set.", allow_module_level=True)


class DummyEngine:
    def __init__(self):
        self.called = False
        self.kwargs = None

    def search(self, *args, **kwargs):
        # record call and return immediately
        self.called = True
        self.kwargs = kwargs


def test_mainwindow_passes_excludes_to_engine(tmp_path):
    """MainWindow が SettingsManager の exclude_extensions と UI のパターンを GrepEngine に渡すことを検証する。"""
    root = tk.Tk()
    app = BaseApplication()

    # 用意した exclude_extensions を設定
    app.settings_manager.set_setting("exclude_extensions", ".log,.tmp", save=False)

    # 置き換え可能なダミーエンジン
    dummy = DummyEngine()
    app.engine = dummy

    mw = MainWindow(root, app)

    # 呼び出し（UI側の除外パターンも渡す）
    mw._on_start_search(
        target_dir=str(tmp_path),
        search_text="X",
        regex_mode=False,
        ignore_case=False,
        whole_word=False,
        exclude_dirs=[".git"],
        exclude_file_patterns=["*.bak"],
    )

    # スレッドで実行されるため少し待つ
    time.sleep(0.2)

    assert dummy.called is True
    # exclude_exts が正しく渡されている
    assert 'exclude_exts' in dummy.kwargs
    assert isinstance(dummy.kwargs['exclude_exts'], list)
    assert '.log' in dummy.kwargs['exclude_exts']
    assert '.tmp' in dummy.kwargs['exclude_exts']
    # ファイルパターンも渡される
    assert 'exclude_file_patterns' in dummy.kwargs
    assert dummy.kwargs['exclude_file_patterns'] == ['*.bak']

    mw.destroy()
    root.destroy()
