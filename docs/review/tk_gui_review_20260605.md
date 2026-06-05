# tk_gui モジュール コードレビュー

**レビュー日**: 2026-06-05  
**対象**: `src/tk_gui/` パッケージおよび関連コア連携部分  
**レビュー方針**: アーキテクチャ、保守性、バグリスク、パフォーマンス、UX の観点

---

## 1. 総合評価

全体として設計方針は明確で、以下の良い実践が見られます。

- **GUIProtocol による抽象化**: Core 層が Tkinter に依存しない設計
- **Adapter パターン**: `TkinterGUIAdapter` で差し替え可能
- **イベント駆動**: `EventDispatcher` による疎結合な通信
- **i18n 対応**: `Translator` による多言語リアルタイム切替
- **テーマ管理の一元化**: `ThemeManager` による Light/Dark 切替

ただし、いくつかの改善点・潜在的バグが確認されました。以下にカテゴリ別に記載します。

---

## 2. アーキテクチャ上の問題

### 2.1 GUIProtocol と TkinterGUIAdapter の乖離 (Medium)

**場所**: `src/core/gui_interface.py` / `src/tk_gui/base/tkinter_adapter.py`

`GUIProtocol` は `initialize`, `run`, `show_message`, `show_error`, `quit` のみを定義していますが、 `MainWindow._on_settings_changed()` では `self.app.gui.apply_theme(theme_name)` を呼び出しています。`apply_theme` は Protocol に含まれていないため、型安全性が損なわれています。

**推奨**: `GUIProtocol` に `apply_theme(theme_name: str) -> None` を追加するか、テーマ適用は `EventDispatcher` 経由で `ThemeManager` が直接受け取る設計にする。

### 2.2 context_menu.py の未使用コード (Low)

**場所**: `src/tk_gui/base/context_menu.py`

`HistoryContextMenu` と `PhraseListContextMenu` は定義されていますが、現在の `main_window.py` や各コンポーネントからは一切参照されていません。`GrepResultListComponent` は独自にインライン `tk.Menu` を作成しており、`BaseContextMenu` を使用していません。

また `HistoryContextMenu` は `self.app.undo_manager`, `self.app.history_handlers`, `self.app.gui.history_component` など、`BaseApplication` には存在しない属性をアクセスしています。これは将来実装のスタブか、別ブランチからのマージ残骸と思われます。

**推奨**: 使用予定がなければ削除、使用予定であれば `BaseApplication` に対応属性の定義と `# type: ignore` の解消を行う。

### 2.3 BaseFrameGUI / BaseToplevelGUI のテーマ適用タイミング (Low)

**場所**: `src/tk_gui/base/base_frame_gui.py`, `base_toplevel_gui.py`

コンストラクタ内で `apply_theme_to_widget_tree(self, THEMES[theme_name])` を呼んでいますが、この時点ではまだ子ウィジェットが構築されていない（`_create_widgets()` はサブクラスで呼ばれる）ため、適用は実質的に自身の背景色のみに限定されます。

**推奨**: コメントにある通り「動的生成のフレーム向け」なら問題ないが、ドキュメントにその旨を明記する。もしくは基底クラスで `_create_widgets()` をフックとして呼び、その後にテーマ適用するテンプレートメソッドパターンを導入する。

---

## 3. スレッドセーフティの問題

### 3.1 バックグラウンドスレッドからの GUI 更新 (High)

**場所**: `src/tk_gui/windows/main_window.py` → `_on_start_search()`

コールバック `on_progress`, `on_result`, `on_complete` は `GrepEngine` 内のワーカースレッドから呼ばれます。現在 `self.after(0, lambda: ...)` でメインスレッドにディスパッチしているのは正しいアプローチです。

ただし `self.after(0, ...)` の `0` はタイマー遅延値であり、Tkinter では `after_idle` と異なります。大量のヒットが短時間で発生した場合、メインループに大量のコールバックがキューイングされ、GUI がフリーズする可能性があります。

**推奨**:
- バッチ処理: 一定件数ごとにまとめて UI を更新するバッファリングの導入
- `after(10, ...)` のように最小間隔を設ける
- 結果をキューに入れ、`after` の定期ポーリングで消費する設計

### 3.2 検索停止後の遅延コールバック (Medium)

**場所**: `src/tk_gui/windows/main_window.py`

`_on_stop_search()` で `engine.stop()` を呼んだ後も、既にスケジュール済みの `after()` コールバック（`_add_to_list`, `_update_progress`）が残存している可能性があります。停止状態を示すフラグを確認してからUIを更新する仕組みが必要です。

**推奨**: `self._is_searching: bool` フラグを導入し、各コールバック内で検証する。

---

## 4. 機能的なバグ・不整合

### 4.1 GrepEngineProtocol と実際の search() シグネチャの不一致 (High)

**場所**: `src/grep/interface.py` vs `src/grep/engine.py`

`GrepEngineProtocol.search()` のシグネチャには `exclude_file_patterns` パラメータが含まれていませんが、`GrepEngine.search()` および `MainWindow._on_start_search()` はこれを使用しています。型チェック (`mypy`) を厳密に実行すると Protocol 違反が検出されます。

**推奨**: `GrepEngineProtocol` に `exclude_file_patterns: Optional[List[str]] = None` を追加する。

### 4.2 SettingsWindow の Save/Cancel ボタンが未翻訳 (Low)

**場所**: `src/tk_gui/windows/settings_window.py`

```python
save_btn = ttk.Button(btn_frame, text="Save", command=self._on_save)
cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
```

他のすべてのラベルは `_t()` で翻訳されているのに、このボタンだけハードコードされています。

**推奨**: `_t('save')`, `_t('cancel')` を使用し、`locales/*.json` に対応キーを追加する。

### 4.3 SettingsWindow での言語変更が即時反映されない可能性 (Medium)

**場所**: `src/tk_gui/windows/settings_window.py`

テーマ変更は `ComboboxSelected` イベントで即座に `_apply_settings(save=False)` が呼ばれますが、言語変更にはこの即時適用バインドがありません。ユーザーが言語を変更して Save を押した場合、`SETTINGS_CHANGED` → `Translator._update_language()` → `LANGUAGE_CHANGED` の順に発火し、全コンポーネントが再描画されますが、設定ウィンドウ自身は `destroy()` されるので実害はありません。ただし UX 的にはプレビューできる方が望ましいです。

### 4.4 os.startfile は Windows 専用 (Medium)

**場所**: `src/tk_gui/components/grep_result_list_component.py`

```python
os.startfile(file_path)
subprocess.run(['explorer', '/select,', os.path.normpath(path)])
```

これらは Windows 以外では動作しません。クロスプラットフォーム対応が必要であれば `platform` 判定が必要です。

**推奨**: 現状 Windows 専用であれば問題ないが、将来のために `webbrowser.open()` や `platform` 分岐を検討する。

---

## 5. 保守性・コード品質

### 5.1 unused import の疑い (Low)

**場所**: 複数ファイル

- `grep_result_list_component.py`: `from typing import List` — Python 3.9+ なら `list` で代用可能（既に `list[str]` 表記が他ファイルで使用されている）
- `phrase_list_component.py`: `from typing import Dict, List` — `Dict` は未使用
- `history_list_component.py`: `from typing import Dict, List` — 使用されているが `list`/`dict` 組み込みで統一可能

### 5.2 ThemeManager でのハードコードされたテーマ名チェック (Low)

**場所**: `src/tk_gui/theme_manager.py`

```python
if theme_name == 'dark':
    style.theme_use('clam')
else:
    style.theme_use('default')
```

テーマが増えた場合にスケールしません。

**推奨**: `THEMES` 辞書にメタデータ（対応する ttk テーマ名）を含める設計にする。

### 5.3 SearchParamComponent の advanced_frame レイアウト (Low)

**場所**: `src/tk_gui/components/search_param_component.py`

`advanced_frame` 内のウィジェットが全て `pack(side=tk.LEFT)` で横並びに配置されています。「除外ディレクトリ」と「除外ファイルパターン」が横一列に並ぶため、ウィンドウ幅が狭い場合にウィジェットが見切れる可能性があります。

**推奨**: `grid` レイアウトで行を分けるか、`LabelFrame` で囲んで視認性を向上させる。

### 5.4 定型文（スニペット）データの外部保存とカテゴリ別管理 (Medium)

**場所**: `src/grep/presets.py` / `src/tk_gui/components/phrase_list_component.py`

現在、定型文（スニペット）データは `config/presets.json` からロードしたものをキャッシュし、フラットなリストとしてUIに表示しています。しかし、ユーザーがGUI上から定型文を追加・削除・編集する機能がなく、またカテゴリ情報が無視されて平坦化されています。

**推奨**:
- スニペットデータを外部データベース（SQLiteなど）やユーザー個別設定（JSON）に保存できるようにし、GUIからの追加・編集・削除（永続化）をサポートする。
- データの保存およびUI表示の際、`presets.json` にあるように「カテゴリ別（プログラミング、ネットワーク、ログ等）」に整理・管理・分類できるようにデータ構造と仕様を明記・設計する。

---

## 6. パフォーマンス懸念

### 6.1 履歴タブの全件再描画 (Low)

**場所**: `src/tk_gui/components/history_list_component.py`

`add_history()` 呼び出しのたびに `_refresh_list()` が全 Treeview アイテムを `delete` → 全件 `insert` します。履歴上限は 50 件なので現状は問題ありませんが、将来上限が増えた場合は差分更新が望ましいです。

### 6.2 テーマ適用の再帰走査 (Low)

**場所**: `src/tk_gui/theme_manager.py`

`apply_theme_to_widget_tree()` はすべてのウィジェットツリーを再帰的に走査します。ウィジェット数が多い場合にレイテンシが生じる可能性がありますが、このアプリの規模では問題ありません。

---

## 7. UX / アクセシビリティ

### 7.1 キーボードショートカット未定義 (Medium)

メニュー項目（Exit, Settings, Search Start/Stop）にアクセラレータキーが定義されていません。

**推奨**: 主要操作に `Ctrl+F` (検索フォーカス), `Ctrl+Enter` (検索開始), `Escape` (検索停止), `Ctrl+,` (設定) などを割り当てる。

### 7.2 検索結果の視覚的フィードバック (Low)

ヒット件数は `status_var` に表示されますが、検索結果ゼロ件の場合に「見つかりませんでした」等のメッセージが明示的に表示されません。`_search_complete(0)` 時に "Complete! hits: 0" とだけ表示されます。

**推奨**: 0 件の場合は専用メッセージを表示する。

### 7.3 プログレスバーの完了後リセット (Low)

検索完了後にプログレスバーは 100% のまま残ります。次の検索開始時に `self.progress_var.set(0)` でリセットされますが、完了後に `progress_var.set(100)` を明示的にセットしておくと UX が改善されます。

---

## 8. セキュリティ

### 8.1 subprocess.run でのコマンドインジェクション (Low)

**場所**: `src/tk_gui/components/grep_result_list_component.py`

```python
subprocess.run(['explorer', '/select,', os.path.normpath(path)])
```

リスト形式のため直接的なインジェクションリスクは低いですが、`path` にユーザー入力由来のパスが含まれるため、`os.path.normpath` による正規化は適切です。現状問題なし。

---

## 9. 改善提案まとめ（優先度順）

| 優先度 | 項目 | 概要 |
|--------|------|------|
| High | 3.1 | 大量ヒット時の GUI フリーズ対策（バッファリング） |
| High | 4.1 | GrepEngineProtocol に `exclude_file_patterns` を追加 |
| Medium | 2.1 | GUIProtocol に `apply_theme` を追加 |
| Medium | 3.2 | 停止後の遅延コールバック制御 |
| Medium | 4.3 | 言語変更のプレビュー対応 |
| Medium | 4.4 | クロスプラットフォーム対応（将来検討） |
| Medium | 7.1 | キーボードショートカットの追加 |
| Low | 2.2 | 未使用の context_menu.py コードの整理 |
| Low | 4.2 | Save/Cancel ボタンの翻訳対応 |
| Low | 5.1 | typing import の整理 |
| Low | 5.3 | advanced_frame のレイアウト改善 |
| Medium | 5.4 | 定型文（スニペット）の外部保存化とカテゴリ別管理の明記 |
| Low | 7.2 | 検索結果 0 件時のメッセージ改善 |

---

## 10. 良い実践として評価できる点

1. **明確な責務分離**: Core / GUI / Engine が明確に分かれており、テスタビリティが高い
2. **イベント駆動設計**: `EventDispatcher` による疎結合な通知機構
3. **国際化の設計**: `Translator(__call__)` による簡潔な翻訳呼び出し + 動的切替
4. **スレッド化された検索**: `threading.Thread(daemon=True)` + `after()` による UI 非ブロッキング設計
5. **テーマの一元管理**: `ThemeManager` がすべてのウィジェットスタイルを責任持つ
6. **カスタムウィジェット (ContextMenuMixin)**: MRO を活用した機能合成の好例
7. **エラーハンドリングの分離**: `error_handler.py` のコールバック方式で GUI 依存を排除
8. **履歴の永続化分離**: `HistoryManager` による独立したデータ管理

---
