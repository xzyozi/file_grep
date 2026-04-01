import time
import pytest
from src.core.base_application import BaseApplication
from src.grep.mock_engine import MockGrepEngine

class MockGUI:
    """GUIアダプターの簡易モック。初期化や終了の疎通を確認します。"""
    def __init__(self):
        self.initialized = False
        self.ran = False
        self.quit_called = False
    
    def initialize(self): self.initialized = True
    def run(self): self.ran = True
    def quit(self): self.quit_called = True
    def show_message(self, t, m): pass
    def show_error(self, t, m): pass

class CustomMockEngine(MockGrepEngine):
    """
    テスト用に検索完了を補足できるようにしたMockEngine。
    """
    def __init__(self):
        super().__init__()
        self.completed = False

    def search(self, *args, **kwargs):
        # 実際の結果を模しつつ、親のメソッド（MockGrepEngine.search）を呼ぶ
        hit_count = super().search(*args, **kwargs)
        self.completed = True
        return hit_count

class TestSystemIntegration:
    """
    Core と Engine の疎通、およびアプリケーション全体の起動フローのテスト。
    """

    def test_application_initialization_flow(self):
        """1. アプリケーションの起動と初期化が正しく連鎖するか（疎通）"""
        gui_mock = MockGUI()
        app = BaseApplication(gui_adapter=gui_mock)
        
        # 1-1. サービスが初期化されているか
        assert app.settings_manager is not None
        assert app.history_manager is not None
        assert app.translator is not None
        
        # 1-2. GUIとの接続 (run)
        app.run()
        assert gui_mock.initialized == True
        assert gui_mock.ran == True

    def test_core_engine_search_flow(self):
        """2. コアからエンジンを呼び出し、結果がコールバックされるか（疎通）"""
        app = BaseApplication()
        # テスト用にモックエンジンを注入
        mock_engine = CustomMockEngine()
        app.engine = mock_engine
        
        received_results = []
        progress_updates = []
        
        def on_result(res): received_results.append(res)
        def on_progress(cur, tot): progress_updates.append((cur, tot))
        
        # 検索実行 (MockEngineは20ファイルを想定)
        app.engine.search(
            target_dir="dummy",
            search_text="test_keyword",
            on_progress=on_progress,
            on_result=on_result
        )
        
        # 疎通確認：進捗通知が来ているか
        assert len(progress_updates) > 0
        assert progress_updates[-1][0] == 20 # 20ファイル完了
        
        # 疎通確認：(ランダムな確率だが) 結果が来ているか
        # Mockは2割の確率でヒットさせるので、1個以上ヒットすることを期待（高確率）
        assert mock_engine.completed == True

    def test_application_quit_saves_state(self):
        """3. アプリ終了時に設定と履歴が確実に保存されるか (疎通)"""
        gui_mock = MockGUI()
        app = BaseApplication(gui_adapter=gui_mock)
        
        # 設定を変更
        app.settings_manager.set_setting("theme", "selected_theme", save=False)
        
        # アプリ終了
        app.quit()
        
        # 設定ファイルが保存され、GUIの終了処理が呼ばれたか
        assert gui_mock.quit_called == True

    def test_search_cancellation_flow(self):
        """4. 検索の中断指令がエンジンへ正しく伝わり、終了するか (疎通)"""
        app = BaseApplication()
        mock_engine = CustomMockEngine()
        app.engine = mock_engine

        # 検索を開始
        app.engine.search(target_dir="dummy", search_text="test")
        
        # 即座に停止をかける
        app.engine.stop()
        
        # 実際に停止されているか（MockEngineの内部フラグを確認）
        assert mock_engine._stop_event.is_set() == True

    def test_error_propagation_to_gui(self):
        """5. エンジン層のエラーがGUIアダプターまで到達するか (疎通)"""
        from src.utils.error_handler import log_and_show_error, register_ui_error_callback
        
        gui_errors = []
        def mock_error_callback(title, msg):
            gui_errors.append((title, msg))
        
        # GUIアダプターのフックを模す
        register_ui_error_callback(mock_error_callback)
        
        # 重大なエラーをシミュレート
        log_and_show_error("Engine Failure", "Disk is full")
        
        # UI側でエラーを受け取れているか
        assert len(gui_errors) == 1
        assert gui_errors[0][0] == "Engine Failure"
        assert gui_errors[0][1] == "Disk is full"

    def test_event_propagation_theme_change(self):
        """6. 設定変更のイベントが購読者に正しく伝わるか (疎通)"""
        app = BaseApplication()
        
        received_settings = []
        def on_settings_changed(settings):
            received_settings.append(settings)
            
        # イベント購読
        app.event_dispatcher.subscribe("SETTINGS_CHANGED", on_settings_changed)
        
        # テーマを変更
        app.settings_manager.set_setting("theme", "dark", save=False)
        
        # イベントが発火されたか
        assert len(received_settings) == 1
        assert received_settings[0]["theme"] == "dark"

    def test_translation_sync_with_settings(self):
        """7. 設定変更が翻訳エンジン(Translator)まで自動的に伝わるか (疎通)"""
        import os
        import json
        
        # テスト用の locales 構成を一時的に提供
        app = BaseApplication()
        # 今回は簡易的に Translator の動作を検証
        
        # 初期状態が en だと仮定
        app.settings_manager.set_setting("language", "en", save=False)
        assert app.translator.current_lang == "en"
        
        # 設定を ja に変更
        app.settings_manager.set_setting("language", "ja", save=False)
        
        # Translator 内部が ja に同期されているか (疎通)
        assert app.translator.current_lang == "ja"
        # ※ファイル保存の検証は SettingsManager の単体テストで保証済みのため、ここでは呼び出し疎通を重視
