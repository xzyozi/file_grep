# コア & GUI 統合テスト計画書 (Core & GUI Integration Test Plan)

本ドキュメントは、アプリケーションの基盤（Core）、GUIフレームワーク、および検索エンジンの三者間が、設計通りに「疎通（Interaction）」し、正しくデータが受け渡されることを確認するための試験項目を定義します。

---

## 1. コア基盤 (Core Services) のユニットテスト
コアクラス単体、およびそれら相互の連携が正しく行われるかを、`pytest` で検証します。

### A. 設定管理 (`SettingsManager`)
- [x] `settings.json` から値を読み込み、変更時にファイルへ書き込まれるか
- [x] 設定変更時に `EventDispatcher` を介して `SETTINGS_CHANGED` イベントが正しく発行されるか

### B. 履歴管理 (`HistoryManager`)
- [x] 新規履歴の追加後、`history.json` に即座に永続化されるか
- [x] 50件（規定値）を超えた場合に、古い履歴から順に削除されるか
- [x] 同一内容（KW, Dir, Regex）の重複追加が防止され、最新が先頭に来るか

### C. 多言語・翻訳 (`Translator`)
- [x] `en.json`, `ja.json` のキーが正しく読み込まれ、`translate('settings')` 等が言語設定に応じた文字列を返すか
- [x] 言語設定が `ja` でもキーが存在しない場合、`en` へフォールバックするか
- [x] 言語変更時に `LANGUAGE_CHANGED` 全体イベントが発行されるか

---

## 2. 統合・疎通試験 (Interaction Tests)
各モジュール間の「繋ぎ込み」が正常であることを検証します。

### A. エンジン ↔ コアの疎通 (Engine-Core Link)
- [x] **検索フロー**: エンジンから `on_progress` 回数が `BaseApplication` を通過し、プログレスバーへ正しく伝わるか
- [x] **検索制御**: 中断指令 (`stop()`) がエンジン内のスレッドへ正しく伝わり、安全に終了するか
- [x] **新オプション連動**: GUIから「大文字小文字の区別」「単語単位」がエンジンへ引数として渡るか

### B. コア ↔ GUI の疎通 (Core-GUI Link)
- [x] **テーマ・言語連動**: `EventDispatcher` 経由の `SETTINGS_CHANGED` 等が全ウィジェットの再構成を起動するか
- [x] **エラー通知連鎖**: エンジン側の非同期エラーが `log_and_show_error` 経由で UI の `messagebox` まで連鎖するか
- [x] **スレッドセーフな更新**: エンジン（サブスレッド）から GUI（メインスレッド）への描画更新が `after()` 経由で安全に行われるか

---

## 3. エンジン詳細・Office パース試験 (Engine & Office Detailed Tests)
特に複雑な位置特定とパフォーマンスに関する試験項目です。

### A. テキストファイル検索 (Improved Grep)
- [x] **メモリ効率**: 巨大ファイル検索時に全読み込みをせず、ストリーム読み込みができているか
- [x] **自動バイナリ判定**: Nullバイト (`\x00`) を含むファイルを自動検知してスキップできるか
- [x] **検索オプション**: 「大文字小文字無視」「単語単位 (Boundaries)」が期待通りにマッチするか

### B. Office ファイル検索 (Detailed Office Parsing)
- [x] **Excel 座標特定**: `Sheet1!A5` のように、正しいシート名とセル番地が `location_display` にセットされるか
- [x] **Excel 数値検索**: 共有文字列以外の、数値型セルからのヒットも取得できるか
- [x] **Word ヘッダー・フッター**: 本文以外の `header/footer.xml` 内のテキストも検索対象に含まれるか

---

## 4. 試験環境・実行ツール
- **自動テスト**: `pytest tests/test_core_logic.py`, `pytest tests/test_integration.py`
- **リント**: `ruff check src`
- **型チェック**: `mypy src`
- **CLI 手動試験**: `python src/grep/cli_test.py`
- **GUI アプリケーション**: `python src/main.py`
