import os
import sys

# プロジェクトルートを Python パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.base_application import BaseApplication
from src.tk_gui.base.tkinter_adapter import TkinterGUIAdapter


def run_app() -> None:
    """アプリケーション本体の起動処理。"""
    # 1. バックエンド基盤 (Core) の生成
    app = BaseApplication()

    # 2. 具体的な GUI 実装 (Tkinter) をアダプター経由で接続
    # 将来的に wxPython などにする場合はここを入れ替える
    gui_adapter = TkinterGUIAdapter(app)
    app.set_gui(gui_adapter)

    # 3. 起動
    app.run()

def main() -> None:
    """エントリポイント"""
    try:
        run_app()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR during application startup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
