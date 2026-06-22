"""
GrepEngine CLI テストツール

本番実装の GrepEngine を使用し、ディレクトリを指定してgrep検索を行う
CLIベースの機能テストスクリプト。

使い方:
    python -m src.grep.cli_test <target_dir> <search_text> [options]

例:
    python -m src.grep.cli_test ./docs "TODO"
    python -m src.grep.cli_test ./src "def\\s+\\w+" -r
    python -m src.grep.cli_test ./src "import" -i --exclude-dirs .git,__pycache__
"""

import argparse
import json
import os
import sys
import time
from typing import Any, List, Optional

# プロジェクトルートをパスに追加して自作モジュールをインポート可能にする
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.grep.engine import GrepEngine, GrepResult


def load_exclude_config() -> dict:
    """config/exclude.json から除外設定を読み込む"""
    config_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'config', 'exclude.json'
    )
    config_path = os.path.abspath(config_path)
    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f'[WARN] 除外設定ファイルの読み込みに失敗: {e}')
    return {}


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(
        description='GrepEngine CLI テストツール - ディレクトリ指定でgrep検索を実行',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python -m src.grep.cli_test ./docs "TODO"
  python -m src.grep.cli_test ./src "class\\s+\\w+" -r
  python -m src.grep.cli_test ./src "import" -i -w
  python -m src.grep.cli_test ./src "error" --exclude-dirs .git,__pycache__ --exclude-exts .log,.tmp
        """,
    )

    # 必須引数
    parser.add_argument('target_dir', help='検索対象のディレクトリパス')
    parser.add_argument('search_text', help='検索キーワード（または正規表現パターン）')

    # 検索オプション
    search_group = parser.add_argument_group('検索オプション')
    search_group.add_argument(
        '-r', '--regex', action='store_true', help='正規表現モードを有効化'
    )
    search_group.add_argument(
        '-i', '--ignore-case', action='store_true', help='大文字小文字を区別しない'
    )
    search_group.add_argument(
        '-w', '--whole-word', action='store_true', help='単語単位で検索する'
    )

    # 除外オプション
    exclude_group = parser.add_argument_group('除外オプション')
    exclude_group.add_argument(
        '--exclude-dirs',
        type=str,
        default=None,
        help='除外するディレクトリ名（カンマ区切り、例: .git,node_modules,__pycache__）',
    )
    exclude_group.add_argument(
        '--exclude-exts',
        type=str,
        default=None,
        help='除外する拡張子（カンマ区切り、例: .log,.tmp,.pyc）',
    )
    exclude_group.add_argument(
        '--exclude-files',
        type=str,
        default=None,
        help='除外するファイル名パターン（カンマ区切り、例: *.min.js,*.map）',
    )
    exclude_group.add_argument(
        '--no-config',
        action='store_true',
        help='config/exclude.json の除外設定を無視する',
    )

    # エンジンオプション
    engine_group = parser.add_argument_group('エンジンオプション')
    engine_group.add_argument(
        '--threads',
        type=int,
        default=4,
        help='並列スレッド数（デフォルト: 4）',
    )

    # 出力オプション
    output_group = parser.add_argument_group('出力オプション')
    output_group.add_argument(
        '--no-progress', action='store_true', help='進捗表示を抑制する'
    )
    output_group.add_argument(
        '--count-only', action='store_true', help='ヒット数のみ表示する'
    )

    return parser.parse_args()


def build_exclude_lists(
    args: argparse.Namespace,
) -> tuple:
    """CLIオプションと設定ファイルから除外リストを構築する"""
    exclude_dirs: Optional[List[str]] = None
    exclude_exts: Optional[List[str]] = None
    exclude_file_patterns: Optional[List[str]] = None

    # 設定ファイルから読み込み
    if not args.no_config:
        config = load_exclude_config()
        config_dirs = config.get('exclude_dirs', [])
        config_exts = config.get('exclude_exts', [])
        if config_dirs:
            exclude_dirs = config_dirs
        if config_exts:
            exclude_exts = config_exts

    # CLIオプションで上書き（指定があればマージ）
    if args.exclude_dirs:
        cli_dirs = [d.strip() for d in args.exclude_dirs.split(',') if d.strip()]
        if exclude_dirs:
            exclude_dirs = list(set(exclude_dirs + cli_dirs))
        else:
            exclude_dirs = cli_dirs

    if args.exclude_exts:
        cli_exts = [e.strip() for e in args.exclude_exts.split(',') if e.strip()]
        if exclude_exts:
            exclude_exts = list(set(exclude_exts + cli_exts))
        else:
            exclude_exts = cli_exts

    if args.exclude_files:
        exclude_file_patterns = [
            p.strip() for p in args.exclude_files.split(',') if p.strip()
        ]

    return exclude_dirs, exclude_exts, exclude_file_patterns


def main() -> None:
    """GrepEngine の動作をターミナルから確認するための本体処理"""
    args = parse_args()

    # ディレクトリの存在確認
    target_dir = os.path.abspath(args.target_dir)
    if not os.path.isdir(target_dir):
        print(f'\n[ERROR] 指定されたディレクトリが存在しません: {target_dir}')
        sys.exit(1)

    # 除外設定の構築
    exclude_dirs, exclude_exts, exclude_file_patterns = build_exclude_lists(args)

    # エンジンの初期化
    engine = GrepEngine(max_threads=args.threads)

    # 検索パラメータの表示
    print('\n' + '=' * 60)
    print('GrepEngine CLI テスト')
    print('=' * 60)
    print(f'  対象ディレクトリ : {target_dir}')
    print(f'  検索テキスト     : {args.search_text}')
    print(f'  正規表現         : {"有効" if args.regex else "無効"}')
    print(f'  大文字小文字無視 : {"有効" if args.ignore_case else "無効"}')
    print(f'  単語単位検索     : {"有効" if args.whole_word else "無効"}')
    print(f'  スレッド数       : {args.threads}')
    if exclude_dirs:
        print(f'  除外ディレクトリ : {", ".join(exclude_dirs)}')
    if exclude_exts:
        print(f'  除外拡張子       : {", ".join(exclude_exts)}')
    if exclude_file_patterns:
        print(f'  除外ファイル     : {", ".join(exclude_file_patterns)}')
    print('-' * 60)

    hit_count = 0
    start_time = time.time()

    def on_progress(current: int, total: int) -> None:
        """進捗コールバック"""
        if not args.no_progress:
            pct = (current / total * 100) if total > 0 else 0
            print(
                f'\r[進捗] {current}/{total} ファイル処理済み ({pct:.1f}%)',
                end='',
                flush=True,
            )

    def on_result(result: GrepResult) -> None:
        """検索結果コールバック"""
        if args.count_only:
            return

        # 進捗表示をクリアしてから結果を出力
        if not args.no_progress:
            print('\r' + ' ' * 60 + '\r', end='')

        # Officeファイルの場合は location_display を表示
        if result.location_display:
            print(f'  {result.file_path} [{result.location_display}]')
        else:
            print(f'  {result.file_path}:{result.line_number}')

        # 行内容を表示（長すぎる場合は切り詰め）
        line = result.line_content.strip()
        if len(line) > 120:
            line = line[:120] + '...'
        print(f'    | {line}')

    def on_complete(total_hits: int) -> None:
        """検索完了コールバック"""
        nonlocal hit_count
        hit_count = total_hits

    def on_error(message: str, error: Exception) -> None:
        """エラーコールバック"""
        # 進捗表示をクリア
        if not args.no_progress:
            print('\r' + ' ' * 60 + '\r', end='')
        print(f'  [WARN] {message}: {error}')

    try:
        engine.search(
            target_dir=target_dir,
            search_text=args.search_text,
            regex_mode=args.regex,
            ignore_case=args.ignore_case,
            whole_word=args.whole_word,
            exclude_dirs=exclude_dirs,
            exclude_exts=exclude_exts,
            exclude_file_patterns=exclude_file_patterns,
            on_progress=on_progress,
            on_result=on_result,
            on_complete=on_complete,
            on_error=on_error,
        )
    except ValueError as e:
        print(f'\n[ERROR] 正規表現エラー: {e}')
        sys.exit(1)
    except KeyboardInterrupt:
        engine.stop()
        print('\n\n[中断] ユーザーにより検索が中断されました。')
        sys.exit(130)

    elapsed = time.time() - start_time

    # 最終行をクリア
    if not args.no_progress:
        print('\r' + ' ' * 60 + '\r', end='')

    # サマリー出力
    print('-' * 60)
    print(f'  合計ヒット数 : {hit_count}')
    print(f'  処理時間     : {elapsed:.3f} 秒')
    print('=' * 60)


if __name__ == '__main__':
    main()
