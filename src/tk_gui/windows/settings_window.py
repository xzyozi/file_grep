from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from src.tk_gui.base.base_toplevel_gui import BaseToplevelGUI

if TYPE_CHECKING:
    from src.core.base_application import BaseApplication
    from src.core.config.settings_manager import SettingsManager


class SettingsWindow(BaseToplevelGUI):
    """
    アプリケーションの設定（テーマ、言語など）を行うウィンドウ。
    """

    def __init__(
        self,
        master: tk.Misc,
        app_instance: BaseApplication,
        settings_manager: SettingsManager,
    ) -> None:
        super().__init__(master, app_instance)

        _t = self.app.translator
        self.title(_t('settings'))
        self.geometry('550x550') # サイズを550x550に調整
        self.settings_manager = settings_manager

        # 値の保持用
        self.theme_var = tk.StringVar(value=self.settings_manager.get_setting("theme"))
        self.language_var = tk.StringVar(value=self.settings_manager.get_setting("language"))
        self.exclude_extensions_var = tk.StringVar(value=self.settings_manager.get_setting("exclude_extensions"))

        self._create_widgets()

    def _create_widgets(self) -> None:
        _t = self.app.translator

        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        # 外観設定
        appearance_frame = ttk.LabelFrame(container, text=_t('theme'), padding=10)
        appearance_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(appearance_frame, text=_t('theme') + ":").grid(row=0, column=0, sticky=tk.W, padx=5)
        theme_combo = ttk.Combobox(
            appearance_frame,
            textvariable=self.theme_var,
            values=['light', 'dark'],
            state='readonly'
        )
        theme_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)
        theme_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_settings(save=False))

        # 言語設定
        lang_frame = ttk.LabelFrame(container, text=_t('language'), padding=10)
        lang_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(lang_frame, text=_t('language') + ":").grid(row=0, column=0, sticky=tk.W, padx=5)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, values=['en', 'ja'], state='readonly')
        lang_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)

        # 除外拡張子設定
        ext_frame = ttk.LabelFrame(container, text=_t('exclude_extensions'), padding=10)
        ext_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # 上部: テキストボックス
        entry_frame = ttk.Frame(ext_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(entry_frame, text=_t('exclude_extensions') + ":").pack(side=tk.LEFT, padx=5)
        ext_entry = ttk.Entry(entry_frame, textvariable=self.exclude_extensions_var)
        ext_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 中央: カテゴリ別ツリー表示
        self.ext_tree = ttk.Treeview(ext_frame, show='tree', height=6)
        self.ext_vsb = ttk.Scrollbar(ext_frame, orient='vertical', command=self.ext_tree.yview)
        self.ext_tree.configure(yscrollcommand=self.ext_vsb.set)
        
        self.ext_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.ext_vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._populate_ext_tree()

        # ダブルクリック・Enterキーで選択状態をトグル
        self.ext_tree.bind('<Double-1>', self._on_tree_click)
        self.ext_tree.bind('<Return>', self._on_tree_click)

        # エントリー値の変更を監視してツリーのチェックマークと同期
        self.exclude_extensions_var.trace_add("write", self._on_entry_changed)

        # 下部ボタン
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        save_btn = ttk.Button(btn_frame, text="Save", command=self._on_save)
        save_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def _populate_ext_tree(self) -> None:
        """設定項目に基づきツリービューを初期構築します。"""
        _t = self.app.translator
        self.ext_categories = [
            {"name": _t("ext_cat_images"), "exts": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico"]},
            {"name": _t("ext_cat_executables"), "exts": [".exe", ".dll", ".so", ".dylib", ".class", ".obj", ".o"]},
            {"name": _t("ext_cat_archives"), "exts": [".zip", ".tar", ".gz", ".rar", ".7z"]},
            {"name": _t("ext_cat_temp_logs"), "exts": [".log", ".bak", ".tmp", ".pyc", ".pyo"]}
        ]
        
        current_exts = [e.strip().lower() for e in self.exclude_extensions_var.get().split(',') if e.strip()]
        current_exts = [('.' + e) if not e.startswith('.') else e for e in current_exts]
        
        self.ext_tree.delete(*self.ext_tree.get_children())
        
        for cat in self.ext_categories:
            cat_name = cat["name"]
            cat_exts = cat["exts"]
            
            # カテゴリ内の選択状態を算出
            checked_count = sum(1 for e in cat_exts if e in current_exts)
            if checked_count == len(cat_exts):
                cat_prefix = "⬛ "
            elif checked_count > 0:
                cat_prefix = "▧ "
            else:
                cat_prefix = "⬜ "
                
            # カテゴリ（親ノード）を追加
            cat_iid = self.ext_tree.insert("", tk.END, text=f"{cat_prefix}{cat_name}", open=True, tags=(cat_name, "category"))
            
            for ext in cat_exts:
                checked = ext in current_exts
                prefix = "⬛ " if checked else "⬜ "
                self.ext_tree.insert(cat_iid, tk.END, text=f"{prefix}{ext}", tags=(ext,))

    def _on_tree_click(self, event: tk.Event) -> None:
        """ツリーの拡張子やカテゴリが選択された際にチェック状態を切り替えてEntryに反映します。"""
        selected = self.ext_tree.selection()
        if not selected:
            return
        
        item_iid = selected[0]
        tags = self.ext_tree.item(item_iid, "tags")
        if not tags:
            return
        
        current_exts = [e.strip().lower() for e in self.exclude_extensions_var.get().split(',') if e.strip()]
        current_exts = [('.' + e) if not e.startswith('.') else e for e in current_exts]
        
        # 親ノード（カテゴリ）の場合
        if "category" in tags:
            cat_name = tags[0]
            target_cat = next((c for c in self.ext_categories if c["name"] == cat_name), None)
            if not target_cat:
                return
            
            cat_exts = target_cat["exts"]
            checked_in_cat = [e for e in cat_exts if e in current_exts]
            
            # 全てチェック済みなら、全てアンチェック
            if len(checked_in_cat) == len(cat_exts):
                for ext in cat_exts:
                    if ext in current_exts:
                        current_exts.remove(ext)
            # 一部、または未チェックなら全てチェック
            else:
                for ext in cat_exts:
                    if ext not in current_exts:
                        current_exts.append(ext)
        # 子ノード（拡張子単体）の場合
        else:
            ext = tags[0]
            if ext in current_exts:
                current_exts.remove(ext)
            else:
                current_exts.append(ext)
            
        self.exclude_extensions_var.set(",".join(current_exts))

    def _on_entry_changed(self, *args) -> None:
        """Entryの変更に合わせてツリーの☑/☐/[-]表記を同期します。"""
        current_exts = [e.strip().lower() for e in self.exclude_extensions_var.get().split(',') if e.strip()]
        current_exts = [('.' + e) if not e.startswith('.') else e for e in current_exts]
        
        for parent_iid in self.ext_tree.get_children():
            parent_tags = self.ext_tree.item(parent_iid, "tags")
            if not parent_tags or "category" not in parent_tags:
                continue
                
            cat_name = parent_tags[0]
            children = self.ext_tree.get_children(parent_iid)
            checked_count = 0
            
            # 子ノードの更新とカウント
            for child_iid in children:
                tags = self.ext_tree.item(child_iid, "tags")
                if tags:
                    ext = tags[0]
                    checked = ext in current_exts
                    if checked:
                        checked_count += 1
                    prefix = "⬛ " if checked else "⬜ "
                    self.ext_tree.item(child_iid, text=f"{prefix}{ext}")
            
            # 親ノード（カテゴリ）の更新
            if checked_count == len(children):
                cat_prefix = "⬛ "
            elif checked_count > 0:
                cat_prefix = "▧ "
            else:
                cat_prefix = "⬜ "
            self.ext_tree.item(parent_iid, text=f"{cat_prefix}{cat_name}")

    def _apply_settings(self, save: bool = False) -> None:
        """現在の入力を設定マネージャーに反映します。"""
        self.settings_manager.set_setting("theme", self.theme_var.get(), save=save)
        self.settings_manager.set_setting("language", self.language_var.get(), save=save)
        self.settings_manager.set_setting("exclude_extensions", self.exclude_extensions_var.get(), save=save)

    def _on_save(self) -> None:
        """設定を保存して閉じます。"""
        self._apply_settings(save=True)
        messagebox.showinfo("Success", "Settings saved successfully.")
        self.destroy()
