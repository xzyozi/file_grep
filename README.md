# 🔍 file_grep

高機能ファイル検索ツール - テキストファイル・Office文書を対象とした、GUI搭載の並列グレップエンジン

## ✨ 主な機能

- **🎯 マルチフォーマット対応**: テキストファイル、Word（`.docx`）、Excel（`.xlsx`）から検索
- **⚙️ 柔軟な検索オプション**:
  - 正規表現サポート
  - 大文字小文字の区別可否
  - 単語単位検索
  - ディレクトリ除外フィルター
- **🚀 高速並列検索**: マルチスレッド処理による効率的なスキャン
- **🎨 テーマ対応**: ダークモード・ライトモード自動切り替え
- **🌐 多言語対応**: 日本語・英語デフォルト搭載
- **💾 履歴・プリセット管理**: 検索履歴、検索条件プリセット保存機能

## 📋 システム要件

- **Python**: 3.8以上
- **OS**: Windows, macOS, Linux

## 🚀 クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/xzyozi/file_grep.git
cd file_grep

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 依存関係

現在、外部ライブラリ不使用の軽量構成です。GUI には標準ライブラリの `tkinter` を使用します。

```bash
# 別途インストール不要 (Python 標準ライブラリのみ)
```

### アプリケーション起動

```bash
# メインアプリケーションを起動
python src/main.py
```

## 📁 プロジェクト構造

```
src/
├── main.py                    # エントリーポイント
├── core/                      # ビジネスロジック基盤
│   ├── base_application.py    # アプリケーション統合管理
│   ├── event_dispatcher.py    # イベント発行・購読機構
│   ├── gui_interface.py       # GUI抽象インターフェース
│   └── config/                # 設定・履歴管理
│       ├── settings_manager.py
│       └── history_manager.py
├── grep/                      # 検索エンジン
│   ├── engine.py              # Grepエンジン（コアロジック）
│   ├── office_parser.py       # Office文書パーサー
│   ├── interface.py           # エンジンインターフェース
│   └── presets.py             # 検索プリセット
├── tk_gui/                    # Tkinter ベース GUI実装
│   ├── base/                  # 基底クラス
│   │   ├── base_frame_gui.py
│   │   ├── base_toplevel_gui.py
│   │   └── tkinter_adapter.py # GUI統合アダプター
│   ├── components/            # 再利用可能なコンポーネント
│   │   ├── search_param_component.py
│   │   ├── grep_result_list_component.py
│   │   ├── history_list_component.py
│   │   └── phrase_list_component.py
│   ├── windows/               # 具体的な画面実装
│   │   ├── main_window.py
│   │   └── settings_window.py
│   ├── theme_manager.py       # テーマ管理（ダークモード等）
│   └── custom_widgets.py      # カスタムウィジェット
└── utils/                     # ユーティリティ
    ├── i18n.py                # 多言語翻訳
    ├── logging_config.py      # ログ設定
    ├── error_handler.py       # エラーハンドリング
    └── undo_manager.py        # undo/redo機構
```

## 🏗️ アーキテクチャ

### 層分け設計

```
┌─────────────────────────────────────┐
│  GUI Layer (Tkinter)                │
│  - MainWindow, SettingsWindow       │
│  - Components (再利用可能)            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Core Application                   │
│  - EventDispatcher                  │
│  - SettingsManager                  │
│  - HistoryManager                   │
│  - GUIAdapter                       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Grep Engine & Office Parser        │
│  - Multithread Search               │
│  - Office Document Support          │
│  - Character Encoding Detection     │
└─────────────────────────────────────┘
```

### 疎結合設計の特徴

- **`BaseApplication`**: コアロジック集約、GUIと検索エンジンの仲介役
- **`EventDispatcher`**: 設定変更・言語切り替えの購読・発行機構
- **`GUIAdapter`**: 将来的なGUIフレームワーク切り替えに対応（現在 Tkinter）

## ⚙️ 設定・多言語

### 言語切り替え

言語ファイルは `locales/` に配置：
- `locales/ja.json` - 日本語
- `locales/en.json` - 英語

### テーマ設定

`settings.json` で管理：
```json
{
    "theme": "dark",      // "dark" または "light"
    "language": "ja"      // "ja" または "en"
}
```

## 🧪 テスト実行

```bash
# 全テスト実行
python -m pytest tests/

# 特定のテストファイル実行
python -m pytest tests/test_grep_engine.py -v

# Linting チェック
ruff check src tests

# 型チェック
mypy src
```

テスト計画の詳細は [docs/test/](docs/test/) を参照してください。

## 📖 ドキュメント

- [GUI 設計書](docs/design/gui_architecture.md) - Tkinter ベース設計
- [セットアップガイド](docs/setup/toml_project_setup.md) - 環境構築手順（Hatch版）
- [依存関係管理](docs/setup/dependency_management.md) - pip-tools による依存管理
- [コア & GUI 統合テスト計画](docs/test/core_and_gui_test_plan.md) - テスト項目
- [Grepエンジン テスト計画](docs/test/grep_engine_test_plan.md) - エンジン仕様

## 🔧 開発ガイド

### 新しい検索オプションの追加

1. [src/grep/engine.py](src/grep/engine.py) の `search()` メソッドに引数追加
2. [src/tk_gui/components/search_param_component.py](src/tk_gui/components/search_param_component.py) で UI コンポーネント追加
3. [tests/test_grep_engine.py](tests/test_grep_engine.py) にテストケース追加

### 新しい言語対応

1. [locales/](locales/) に新言語JSONファイル作成（例：`fr.json`）
2. 既存言語ファイルの構造を参考に翻訳キーを記載
3. [src/utils/i18n.py](src/utils/i18n.py) で言語リストに追加

### GUI フレームワークの切り替え（将来）

現在のTkinterから別フレームワーク（wxPython等）への移行は、以下の手順で可能：

1. `src/tk_gui/` を新フレームワーク実装で置き換え
2. 新フレームワーク用の `GUIAdapter` を実装
3. `BaseApplication.set_gui()` で新アダプターを指定

## 📝 ライセンス

[LICENSE ファイルを参照](LICENSE)


## 🤝 コントリビューション

バグ報告や機能提案は [Issues](https://github.com/xzyozi/file_grep/issues) まで。
