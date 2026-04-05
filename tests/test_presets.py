import json
import os
import pytest
from src.grep.presets import SearchPresets

@pytest.fixture
def temp_presets(tmp_path, monkeypatch):
    """テスト用の一時的な presets.json を作成し、SearchPresets に適用するフィクスチャ。"""
    # テストデータ
    mock_data = [
        {
            "category": "Test Category",
            "items": [
                ["Test Label 1", "pattern1", True],
                ["Test Label 2", "pattern2", False]
            ]
        }
    ]
    
    # プロジェクトルートとして扱われる場所に config/ フォルダを作って保存
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    presets_file = config_dir / "presets.json"
    presets_file.write_text(json.dumps(mock_data), encoding='utf-8')
    
    # SearchPresets 内のパス設定とキャッシュをリセット (モンキーパッチ)
    monkeypatch.setattr(SearchPresets, "PRESETS_FILE", str(presets_file))
    monkeypatch.setattr(SearchPresets, "_presets", None)
    
    return presets_file

def test_get_all_loads_from_json(temp_presets):
    """1. get_all が JSON からすべてのアイテムを正しく読み込めるか検証。"""
    presets = SearchPresets.get_all()
    
    assert len(presets) == 2
    assert presets[0] == ("Test Label 1", "pattern1", True)
    assert presets[1] == ("Test Label 2", "pattern2", False)

def test_get_by_label(temp_presets):
    """2. ラベル名によるパターン検索が正しく機能するか検証。"""
    pattern, is_regex = SearchPresets.get_by_label("Test Label 1")
    assert pattern == "pattern1"
    assert is_regex is True
    
    # 存在しないラベル
    pattern, is_regex = SearchPresets.get_by_label("No such label")
    assert pattern == ""
    assert is_regex is False

def test_invalid_json_handling(tmp_path, monkeypatch):
    """3. 不正な形式の JSON ファイルがある場合の堅牢性を検証。"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    bad_file = config_dir / "bad_presets.json"
    bad_file.write_text("This is not JSON", encoding='utf-8')
    
    monkeypatch.setattr(SearchPresets, "PRESETS_FILE", str(bad_file))
    monkeypatch.setattr(SearchPresets, "_presets", None)
    
    # エラーにならず、空リストが返ることを期待
    presets = SearchPresets.get_all()
    assert presets == []

def test_missing_file_handling(monkeypatch):
    """4. ファイルが存在しない場合に空リストを返すか検証。"""
    monkeypatch.setattr(SearchPresets, "PRESETS_FILE", "non_existent_file.json")
    monkeypatch.setattr(SearchPresets, "_presets", None)
    
    presets = SearchPresets.get_all()
    assert presets == []
