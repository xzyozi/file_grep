import os
import json
import pytest
from src.grep.engine import GrepEngine
from src.core.event_dispatcher import EventDispatcher
from src.core.config.settings_manager import SettingsManager
from src.core.config.history_manager import HistoryManager
from src.utils.i18n import Translator

@pytest.fixture
def temp_config_dir(tmp_path):
    """テスト用の設定ファイル用一時ディレクトリを作成する"""
    return tmp_path

class TestEventDispatcher:
    def test_subscribe_and_dispatch(self):
        dispatcher = EventDispatcher()
        received_data = []

        def listener(data):
            received_data.append(data)

        dispatcher.subscribe("TEST_EVENT", listener)
        dispatcher.dispatch("TEST_EVENT", "Hello World")

        assert len(received_data) == 1
        assert received_data[0] == "Hello World"

    def test_unsubscribe(self):
        dispatcher = EventDispatcher()
        received_data = []

        def listener(data):
            received_data.append(data)

        dispatcher.subscribe("TEST_EVENT", listener)
        dispatcher.unsubscribe("TEST_EVENT", listener)
        dispatcher.dispatch("TEST_EVENT", "No one should hear this")

        assert len(received_data) == 0

class TestSettingsManager:
    def test_load_save_settings(self, temp_config_dir):
        dispatcher = EventDispatcher()
        # プロジェクトルートに依存させないように一時パスを渡す
        config_file = temp_config_dir / "settings_test.json"
        
        # モックの絶対パスをシミュレート
        manager = SettingsManager(dispatcher, config_name=str(config_file))
        
        # 値のセット
        manager.set_setting("theme", "dark", save=True)
        
        # ファイルが生成されているか
        assert os.path.exists(str(config_file))
        
        # 再度ロードして値が一致するか
        new_manager = SettingsManager(dispatcher, config_name=str(config_file))
        assert new_manager.get_setting("theme") == "dark"

    def test_settings_changed_event(self, temp_config_dir):
        dispatcher = EventDispatcher()
        config_file = temp_config_dir / "settings_event.json"
        manager = SettingsManager(dispatcher, config_name=str(config_file))
        
        event_received = []
        def on_change(settings):
            event_received.append(settings)
            
        dispatcher.subscribe("SETTINGS_CHANGED", on_change)
        manager.set_setting("language", "ja")
        
        assert len(event_received) == 1
        assert event_received[0]["language"] == "ja"

class TestHistoryManager:
    def test_add_entry_and_limit(self, temp_config_dir):
        history_file = temp_config_dir / "history_test.json"
        # max_items を 5 に制限してテスト
        manager = HistoryManager(filename=str(history_file), max_items=5)
        
        # 6件追加
        for i in range(6):
            manager.add_entry(f"keyword_{i}", "C:/test", False)
            
        history = manager.get_all()
        # 5件に制限されているか
        assert len(history) == 5
        # 最新が先頭 (keyword_5) か
        assert history[0]["keyword"] == "keyword_5"

    def test_duplicate_handling(self, temp_config_dir):
        history_file = temp_config_dir / "history_dup.json"
        manager = HistoryManager(filename=str(history_file))
        
        # 同じキーワードを2回追加
        manager.add_entry("unique", "C:/test", True)
        manager.add_entry("unique", "C:/test", True)
        
        history = manager.get_all()
        # 重複が排除され、1件のみか
        assert len(history) == 1

class TestTranslator:
    def test_translation_and_fallback(self, temp_config_dir):
        # テスト用の locales フォルダとファイルを作成
        locales_dir = temp_config_dir / "locales"
        locales_dir.mkdir()
        
        en_content = {"save": "Save", "only_en": "Only English"}
        ja_content = {"save": "保存"}
        
        (locales_dir / "en.json").write_text(json.dumps(en_content), encoding="utf-8")
        (locales_dir / "ja.json").write_text(json.dumps(ja_content), encoding="utf-8")
        
        dispatcher = EventDispatcher()
        settings_file = temp_config_dir / "settings_i18n.json"
        settings = SettingsManager(dispatcher, config_name=str(settings_file))
        settings.set_setting("language", "ja")
        
        translator = Translator(settings, locales_dir=str(locales_dir))
        
        # 日本語がある場合は日本語
        assert translator.translate("save") == "保存"
        # 日本語にない場合は英語へフォールバック
        assert translator.translate("only_en") == "Only English"
        # どちらにもない場合はキーをそのまま返す
        assert translator.translate("unknown") == "unknown"

class TestGrepEngine:
    def test_exclude_directories(self, tmp_path):
        """除外ディレクトリ指定が正しく機能するか検証する。"""
        # テスト用ディレクトリ構造の作成
        # root/
        #   target_file.txt (hit!)
        #   node_modules/
        #     ignored_file.txt (should be skipped)
        #   .git/
        #     ignored_git.txt (should be skipped)
        
        root = tmp_path / "root"
        root.mkdir()
        (root / "target_file.txt").write_text("find_me", encoding="utf-8")
        
        nm_dir = root / "node_modules"
        nm_dir.mkdir()
        (nm_dir / "ignored_file.txt").write_text("find_me", encoding="utf-8")
        
        git_dir = root / ".git"
        git_dir.mkdir()
        (git_dir / "ignored_git.txt").write_text("find_me", encoding="utf-8")
        
        engine = GrepEngine()
        results = []
        
        # 除外指定なし
        engine.search(
            target_dir=str(root),
            search_text="find_me",
            on_result=lambda r: results.append(r)
        )
        assert len(results) == 3
        
        # 除外指定あり (.git と node_modules)
        results = []
        engine.search(
            target_dir=str(root),
            search_text="find_me",
            exclude_dirs=["node_modules", ".git"],
            on_result=lambda r: results.append(r)
        )
        # 除外されたため、ルート直下の1件のみヒットするはず
        assert len(results) == 1
        assert os.path.basename(results[0].file_path) == "target_file.txt"
