**要約**
- **目的**: `settings.json` / `history.json`とは別に、除外ディレクトリと除外拡張子を保存する専用設定ファイルを作成して管理できるようにする。

**現状**
- 除外ディレクトリ・除外拡張子はコード内の定数で定義されている。
- 除外ディレクトリは設定画面から編集可能だが、起動時にはコード内の固定値が利用されるため永続化された外部設定からは読み込まれていない。
- grepエンジンは現状、外部からの除外リストを引数で受け取る実装になっていない（変更予定）。

**要件**
1. 起動時に除外ディレクトリと除外拡張子を外部設定ファイルから読み込めること。
2. アプリ内で設定を変更した場合、該当ファイルへ書き戻し可能であること（任意、将来的にUIから保存）。
3. 既存の `settings.json` と `history.json` とは別ファイルに保存すること（例: `exclude_settings.json` または `config/exclude.json`）。
4. 必要に応じて読み書き責務のみを持つファイル操作クラス（File I/Oユーティリティ）を用意できること。
5. 設定を取り扱う `Config` クラスを作成し、アプリ全体で1つの責務に集中させる（読み込み・キャッシュ・保存の責任を持つ）。
6. grepエンジン（`src/grep/engine.py`）は、外部から `exclude_dir` と `exclude_ext` を引数で受け取れるようにする。

**設計案**
- ファイル: `config/exclude.json`（JSON形式）
  - keys: `exclude_dirs: string[]`, `exclude_exts: string[]`
- `src/config/config_manager.py`（新規）
  - クラス: `ConfigManager`
    - `load(path: str) -> ConfigModel`：指定パスから読み込み（デフォルトパスは `config/exclude.json`）
    - `save(path: str, model: ConfigModel) -> None`：書き込み
    - 内部で簡単なバリデーションとデフォルト適用を実施
- `src/config/file_store.py`（新規、必要なら）
  - 単純な読み書きクラス（JSONの読み込み・書き込みのみ）
  - 例: `read_json(path)`, `write_json(path, obj)`
- `ConfigModel` は単純な dataclass/辞書で `exclude_dirs` と `exclude_exts` を保持

**実装タスク（推奨順）**
1. ドキュメント追加（本ファイル）：要件の確定。
2. `config/exclude.json` の雛形ファイルを作成（空の配列を入れる）。
3. `src/config/config_manager.py` を実装（`load`/`save`、デフォルトパス）。
4. 必要なら `src/config/file_store.py` を実装してI/Oを分離。
5. `src/grep/engine.py` のコンストラクタ／APIを変更して `exclude_dir` / `exclude_ext` を引数で受け取るようにする。既存コードとの互換性維持のためデフォルト値は現行定数を使用。
6. アプリ起動処理（`src/main.py` 等）で `ConfigManager.load()` を呼び、読み込んだ設定をエンジンに渡す。
7. 単体テストの追加：`tests/test_grep_engine.py` と `tests/test_presets.py` などで読み込みとエンジンの動作を確認。

**ブランチ反映方針**
- 各既存ブランチごとに順次反映する。まずは `main` ブランチにドキュメントと雛形ファイルを追加し、`config_manager` の実装を小さく分けてPRすることを推奨。

**ファイル配置案（例）**
- `config/exclude.json` (new)
- `src/config/config_manager.py` (new)
- `src/config/file_store.py` (optional)

**注意点 / 備考**
- 既存の定数を削除する前に、`ConfigManager` の読み込みに失敗した時のフォールバック（既存定数）を残すこと。
- 設定読み込みはアプリ起動時に1回行い、実行時は `ConfigManager` のキャッシュを使う設計が望ましい。
- 設定ファイルフォーマットは簡潔に保ち、将来的なキー追加に耐えられる拡張性を確保する。

---
作業を続けて、まずは `config/exclude.json` の雛形を追加し、その後 `ConfigManager` を実装しますか？
