import os

import pytest
import tkinter as tk
from src.tk_gui.components.search_param_component import SearchParamComponent
from src.tk_gui.windows.settings_window import SettingsWindow
from src.core.base_application import BaseApplication
from src.core.config.settings_manager import SettingsManager

if not os.environ.get("DISPLAY"):
    pytest.skip("Skipping UI tests because no DISPLAY is set.", allow_module_level=True)

class MockGUIAdapter:
    def initialize(self): pass
    def run(self): pass
    def quit(self): pass

@pytest.fixture
def app_root():
    """Tkinterのルート要素とアプリケーションインスタンスを提供するフィクスチャ。"""
    root = tk.Tk()
    app = BaseApplication(gui_adapter=MockGUIAdapter())
    yield root, app
    root.destroy()

def test_search_param_exclude_dirs_parsing(app_root):
    """詳細設定の除外ディレクトリ（カンマ区切り）が正しくリストに変換されるか検証。"""
    root, app = app_root
    
    received_params = {}
    def mock_on_start(directory, text, regex, ignore_case, whole_word, exclude_dirs):
        received_params['exclude_dirs'] = exclude_dirs

    # コンポーネント作成
    comp = SearchParamComponent(root, app, on_start=mock_on_start, on_stop=lambda: None)
    
    # ユーザー入力をシミュレート: カンマ区切り、スペース混じり、空要素あり
    comp.exclude_dirs_var.set(" .git,  node_modules, , bin ")
    
    # 検索開始ボタンクリック相当の処理
    comp._on_start_btn_click()
    
    # 期待される結果: 前後のスペースが消え、空要素が除外されていること
    expected = [".git", "node_modules", "bin"]
    assert received_params['exclude_dirs'] == expected

def test_advanced_toggle_logic(app_root):
    """詳細設定ボタンのクリックで表示フラグとgrid状態が切り替わるか検証。"""
    root, app = app_root
    comp = SearchParamComponent(root, app, on_start=lambda *a: None, on_stop=lambda: None)
    
    # 初期状態は非表示
    assert comp.show_advanced is False
    # grid_info が空なら配置されていない
    assert not comp.advanced_frame.grid_info()
    
    # トグル実行 (ON)
    comp._toggle_advanced()
    assert comp.show_advanced is True
    # rowの値はintとして比較
    assert int(comp.advanced_frame.grid_info()['row']) == 3
    
    # トグル実行 (OFF)
    comp._toggle_advanced()
    assert comp.show_advanced is False
    assert not comp.advanced_frame.grid_info()


def test_settings_window_exclude_extensions_save(app_root):
    """SettingsWindow が拡張子除外設定を SettingsManager に保存できるか検証。"""
    root, app = app_root
    settings_manager = SettingsManager(app.event_dispatcher)
    
    # SettingsWindow を作成
    settings_win = SettingsWindow(root, app, settings_manager)
    
    # 拡張子除外を設定
    test_exts = ".log,.bak,.tmp"
    settings_win.exclude_extensions_var.set(test_exts)
    
    # Save ボタンのコールバックを直接呼び出し
    settings_win._apply_settings(save=True)
    
    # 設定が保存されたか確認
    assert settings_manager.get_setting("exclude_extensions") == test_exts
    
    settings_win.destroy()


def test_settings_window_excludes_extensions_load_default(app_root):
    """SettingsWindow が SettingsManager のデフォルト値から拡張子除外を読み込むか検証。"""
    root, app = app_root
    settings_manager = SettingsManager(app.event_dispatcher)
    
    # 事前に値を設定
    settings_manager.set_setting("exclude_extensions", ".cache,.tmp", save=False)
    
    # SettingsWindow を作成 (初期化時に値が読み込まれる)
    settings_win = SettingsWindow(root, app, settings_manager)
    
    # 設定が正しく読み込まれたか確認
    assert settings_win.exclude_extensions_var.get() == ".cache,.tmp"
    
    settings_win.destroy()
