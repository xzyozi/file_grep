# GUI 基本設計 (Tkinter Architecture)

プロジェクトの一新に伴い、UIフレームワークを Tkinter へ移行し、再利用性とメンテナンス性を重視した設計を導入しました。

## 📁 ディレクトリ構造
`src/tk_gui/` 以下を機能ごとに分割しています。

- `base/`: GUI要素（Frame, Toplevel 等）の共通基底クラス
- `components/`: ボタン、リストなどの再利用可能なUIコンポーネント
- `windows/`: メインウィンドウや設定画面などの具体的な画面実装
- `theme_manager.py`: ダークモードや配色の管理。各ウィジェットへの自動適用を担う。
- `custom_widgets.py`: プロジェクト固有のカスタムウィジェット群。

## 🧱 主要な基底クラス

### 1. `BaseFrameGUI` (`src/tk_gui/base/base_frame_gui.py`)
`tkinter.Frame` を継承したクラスです。
- 各機能をコンポーネント化する際のベースとして使用。
- `app_instance` を保持し、アプリケーション全体のステートやロジックに安全にアクセスできます。
- エラーハンドリングのための `log_and_show_error` が標準で組み込まれています。

### 2. `BaseToplevelGUI` (`src/tk_gui/base/base_toplevel_gui.py`)
`tkinter.Toplevel` を継承した、ポップアップやサブウィンドウ用の基底クラスです。
- ウィンドウの生成時に `ThemeManager` を介して、現在のテーマ（カラーパレット）をウィジェットツリーに自動適用します。

## 🎨 デザインポリシー
1. **テーマの一貫性**: `ThemeManager` により一括でカラーリングを制御。
2. **疎結合な設計**: GUIは `BaseApplication` を介してのみビジネスロジックとやり取りします。
3. **統一されたエラー通知**: GUI上の例外発生時、一貫したUI/ログ出力でユーザーへ通知します。
