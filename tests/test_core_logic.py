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
    def test_exclude_directories_deep_and_exact(self, tmp_path):
        """除外ディレクトリ指定が深層および名前の完全一致で機能するか検証する。"""
        # root/
        #   target.txt (HIT)
        #   subdir/
        #     target.txt (HIT)
        #     node_modules/
        #       ignored.txt (SKIP)
        #   binary/ (名前の一部が一致するが除外対象ではない)
        #     target.txt (HIT)
        
        root = tmp_path / "root"
        root.mkdir()
        (root / "target.txt").write_text("match", encoding="utf-8")
        
        subdir = root / "subdir"
        subdir.mkdir()
        (subdir / "target.txt").write_text("match", encoding="utf-8")
        
        nm_dir = subdir / "node_modules"
        nm_dir.mkdir()
        (nm_dir / "ignored.txt").write_text("match", encoding="utf-8")
        
        bin_dir = root / "binary"
        bin_dir.mkdir()
        (bin_dir / "target.txt").write_text("match", encoding="utf-8")
        
        engine = GrepEngine()
        results = []
        
        # 'node_modules' を除外 (bin は除外しない)
        engine.search(
            target_dir=str(root),
            search_text="match",
            exclude_dirs=["node_modules"],
            on_result=lambda r: results.append(r)
        )
        
        # 期待値: 
        # root/target.txt (OK)
        # root/subdir/target.txt (OK)
        # root/binary/target.txt (OK - 'bin'ではないため)
        # ※ root/subdir/node_modules/ignored.txt (SKIP)
        assert len(results) == 3
        
        paths = [os.path.basename(os.path.dirname(r.file_path)) for r in results]
        assert "node_modules" not in paths
        assert "binary" in paths
        assert "subdir" in paths
        assert "root" in [os.path.basename(os.path.dirname(r.file_path)) if os.path.basename(os.path.dirname(r.file_path)) != "root" else "root" for r in results]
