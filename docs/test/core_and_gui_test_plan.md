# コア & GUI 統合テスト計画書 (Core & GUI Integration Test Plan)

本ドキュメントは、アプリケーションの基盤（Core）、GUIフレームワーク、および検索エンジンの三者間が、設計通りに「疎通（Interaction）」し、正しくデータが受け渡されることを確認するための試験項目を定義します。

---

## 1. コア基盤 (Core Services) のユニットテスト
コアクラス単体、およびそれら相互の連携が正しく行われるかを、`pytest` で検証します。

### A. 設定管理 (`SettingsManager`)
- [ ] `settings.json` から値を読み込み、変更時にファイルへ書き込まれるか
- [ ] 設定変更時に `EventDispatcher` を介して `SETTINGS_CHANGED` イベントが正しく発行されるか

### B. 履歴管理 (`HistoryManager`)
- [ ] 新規履歴の追加後、`history.json` に即座に永続化されるか
- [ ] 50件（規定値）を超えた場合に、古い履歴から順に削除されるか
- [ ] 同一内容（KW, Dir, Regex）の重複追加が防止され、最新が先頭に来るか

### C. 多言語・翻訳 (`Translator`)
- [ ] `en.json`, `ja.json` のキーが正しく読み込まれ、`translate('settings')` 等が言語設定に応じた文字列を返すか
- [ ] 言語設定が `ja` でもキーが存在しない場合、`en` へフォールバックするか
- [ ] 言語変更時に `LANGUAGE_CHANGED` 全体イベントが発行されるか

---

## 2. 統合・疎通試験 (Interaction Tests)
各モジュール間の「繋ぎ込み」が正常であることを検証します。

### A. エンジン ↔ コアの疎通 (Engine-Core Link)
- [ ] `BaseApplication` が環境に応じて `GrepEngine` または `MockGrepEngine` を正しく選択・生成するか
- [ ] 検索開始時に、エンジンから `on_progress` 回数が `BaseApplication` の受け口を介して正しくカウント・通知されるか
- [ ] 検索中に `stop()` 指令がコアから発行された際、エンジンが即座に停止し、停止完了通知が返るか

### B. コア ↔ GUI の疎通 (Core-GUI Link)
- [ ] **テーマ連動**: `SettingsManager` でテーマを変更した際、`ThemeManager` がそれを検知し、全ウィジェットの色設定を再構成するか
- [ ] **エラー通知連鎖**: エンジンの実行スレッド内で例外が発生した際、`log_and_show_error` が `TkinterGUIAdapter` の `messagebox` を呼び出してユーザーに通知するか
- [ ] **UI更新の安全性**: 別スレッド（エンジン側）からの進捗通知が、`after()` メソッドを介してメインスレッドで安全に描画更新（プログレスバー等）されるか

---

## 3. 手動連動試験 (Manual Feature Testing)
実際の操作を通じて、エンドツーエンドの挙動を最終確認します。

### A. タブ・コンポーネント連動
- [ ] **履歴からの復元**: 履歴一覧のダブルクリックで、検索ディレクトリとキーワードが入力欄に正しくセットされるか
- [ ] **スニペット適用**: 定型文一覧のダブルクリックで、複雑な正規表現パターンが検索欄にセットされ、正規表現チェックが自動ONになるか
- [ ] **結果表示**: 検索完了後、`Treeview` にファイル名・行番号・内容が期待通り並び、ダブルクリックでファイルが起動するか（`os.startfile` 疎通）

---

## 4. 試験環境・実行ツール
- **自動テスト**: `pytest tests/test_core_logic.py`
- **リント**: `ruff check src`
- **型チェック**: `mypy src`
- **CLI 手動試験**: `python src/grep/cli_test.py`
- **GUI アプリケーション**: `python src/main.py`
