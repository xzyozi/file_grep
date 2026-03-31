import sys
import os
import argparse
from typing import Optional

# プロジェクトルートをパスに追加して自作モジュールをインポート可能にする
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 本番のエンジン実装 (engine.py) がまだの場合は ImportError になるため、
# 開発中はインターフェースを確認できるよう考慮。
try:
    from src.grep.engine import GrepEngine
except ImportError:
    GrepEngine = None

def main():
    """GrepEngine の動作をターミナルから確認するための本体処理"""
    parser = argparse.ArgumentParser(description="GrepEngine CLI Test Tool")
    parser.add_argument("target", help="検索対象のディレクトリパス")
    parser.add_argument("text", help="検索キーワード")
    parser.add_argument("-r", "--regex", action="store_true", help="正規表現モードを有効化")
    args = parser.parse_args()

    if GrepEngine is None:
        print("\n[CAUTION] src/grep/engine.py がまだ実装されていません。")
        print("エンジン本体を実装した後に再度実行してください。")
        return

    # 実装予定の GrepEngine をインスタンス化
    engine = GrepEngine()
    
    print(f"\n>>> 検索を開始します: '{args.text}' (target: {args.target})")
    print("-" * 50)

    def on_progress(current: int, total: int):
        """プログレスバー代わりの進捗コールバック"""
        print(f"\r[Progress] {current}/{total} ファイル走査中...", end="", flush=True)

    def on_result(result):
        """検索結果（ヒット）時のコールバック"""
        print(f"\n[Found] {result.file_path}:{result.line_number}")
        print(f"    Line: {result.line_content.strip()}")

    def on_complete(total_hits: int):
        """全検索終了時のコールバック"""
        print("\n" + "-" * 50)
        print(f">>> 検索が完了しました。合計ヒット数: {total_hits}")

    try:
        engine.search(
            target_dir=args.target,
            search_text=args.text,
            regex_mode=args.regex,
            on_progress=on_progress,
            on_result=on_result,
            on_complete=on_complete
        )
    except KeyboardInterrupt:
        print("\n\n!! 検索がユーザーにより中断されました。")
    except Exception as e:
        print(f"\n\n!! 検索中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
