import json
import os
import pytest
from src.grep.presets import SearchPresets

@pytest.fixture
def mock_presets_env(tmp_path, monkeypatch):
    """テスト用の config/presets.json 環境を構築するフィクスチャ。"""
    # 実際と同じ config/ 構造をシミュレート
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    presets_file = config_dir / "presets.json"
    
    data = [
        {
            "category": "Test Cat",
            "items": [
                ["Hit One", r"^HIT1", True],
                ["Hit Two", r"HIT2$", False]
            ]
        }
    ]
    presets_file.write_text(json.dumps(data), encoding='utf-8')
    
    # 既存のキャッシュをクリアし、パス設定を一時的に上書き
    monkeypatch.setattr(SearchPresets, "_presets", None)
    monkeypatch.setattr(SearchPresets, "PRESETS_FILE", str(presets_file))
    
    return presets_file

def test_load_all_presets_from_custom_path(mock_presets_env):
    """1. 指定したパスから正しくすべてのプリセットが読み込まれるか。"""
    all_presets = SearchPresets.get_all()
    
    assert len(all_presets) == 2
    assert all_presets[0] == ("Hit One", r"^HIT1", True)
    assert all_presets[1] == ("Hit Two", r"HIT2$", False)

def test_get_by_label_functionality(mock_presets_env):
    """2. ラベル指定での検索が期待通りにパターンとフラグを返すか。"""
    pattern, is_regex = SearchPresets.get_by_label("Hit One")
    assert pattern == r"^HIT1"
    assert is_regex is True
    
    # 存在しないラベルの場合
    pattern, is_regex = SearchPresets.get_by_label("NonExistent")
    assert pattern == ""
    assert is_regex is False

def test_handling_invalid_json(tmp_path, monkeypatch):
    """3. JSON が破壊されている場合にアプリケーションが停止せず、空リストを返すか。"""
    bad_file = tmp_path / "broken.json"
    bad_file.write_text("NOT A JSON FILE CONTENT", encoding='utf-8')
    
    monkeypatch.setattr(SearchPresets, "_presets", None)
    monkeypatch.setattr(SearchPresets, "PRESETS_FILE", str(bad_file))
    
    # 例外がスローされず、空リストが返ることを確認
    results = SearchPresets.get_all()
    assert results == []

def test_caching_mechanism(mock_presets_env):
    """4. 二回目以降の呼び出しでディスクアクセスをせず、キャッシュが利用されているか。"""
    # 初回呼び出し
    first_call = SearchPresets.get_all()
    
    # テストファイルを削除
    os.remove(str(mock_presets_env))
    
    # 二回目呼び出し。キャッシュされていればファイルがなくても取れる
    second_call = SearchPresets.get_all()
    
    assert first_call == second_call
    assert len(second_call) == 2
