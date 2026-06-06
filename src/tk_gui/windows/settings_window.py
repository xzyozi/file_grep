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
        self.appearance_frame = ttk.LabelFrame(container, text=_t('theme'), padding=10)
        self.appearance_frame.pack(fill=tk.X, pady=(0, 10))

        self.theme_label = ttk.Label(self.appearance_frame, text=_t('theme') + ":")
        self.theme_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        theme_combo = ttk.Combobox(
            self.appearance_frame,
            textvariable=self.theme_var,
            values=['light', 'dark'],
            state='readonly'
        )
        theme_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)
        # テーマ選択時、設定の適用とチェックボタンテーマの適用を行う
        theme_combo.bind('<<ComboboxSelected>>', lambda e: (self._apply_settings(save=False), self._apply_cb_theme()))

        # 言語設定
        self.lang_frame = ttk.LabelFrame(container, text=_t('language'), padding=10)
        self.lang_frame.pack(fill=tk.X, pady=(0, 10))

        self.lang_label = ttk.Label(self.lang_frame, text=_t('language') + ":")
        self.lang_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        lang_combo = ttk.Combobox(self.lang_frame, textvariable=self.language_var, values=['en', 'ja'], state='readonly')
        lang_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)
        # 言語選択時、設定の適用とUIのリアルタイム再翻訳を行う
        lang_combo.bind('<<ComboboxSelected>>', lambda e: (self._apply_settings(save=False), self._on_language_changed()))

        # 下部ボタンを先に配置（つぶれ防止）
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        self.save_btn = ttk.Button(btn_frame, text=_t('save'), command=self._on_save)
        self.save_btn.pack(side=tk.RIGHT, padx=5)

        self.cancel_btn = ttk.Button(btn_frame, text=_t('cancel'), command=self.destroy)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

        # 除外拡張子設定（残りの領域をいっぱいに広げる）
        self.ext_frame = ttk.LabelFrame(container, text=_t('exclude_extensions'), padding=10)
        self.ext_frame.pack(fill=tk.BOTH, expand=True)

        # 上部: テキストボックス
        entry_frame = ttk.Frame(self.ext_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 5))
        self.ext_label = ttk.Label(entry_frame, text=_t('exclude_extensions') + ":")
        self.ext_label.pack(side=tk.LEFT, padx=5)
        ext_entry = ttk.Entry(entry_frame, textvariable=self.exclude_extensions_var)
        ext_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 中央: スクロール可能なチェックボックスリスト (Canvas & Scrollbar)
        self.canvas = tk.Canvas(self.ext_frame, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.ext_frame, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # マウスホイールイベントのバインド (マウスオーバー時のみ有効化)
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.cb_widgets = []
        self.cat_vars = {}
        self.ext_vars = {}

        self._populate_ext_list()

        # エントリー値の変更を監視してチェックボックスと同期
        self.exclude_extensions_var.trace_add("write", self._on_entry_changed)

        # 初回のチェックボタン配色適用
        self._apply_cb_theme()

    def _populate_ext_list(self) -> None:
        """設定項目に基づきスクロールフレーム内に本物のチェックボタンを構築します。"""
        _t = self.app.translator
        self.ext_categories = [
            {"name": _t("ext_cat_images"), "exts": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico"]},
            {"name": _t("ext_cat_executables"), "exts": [".exe", ".dll", ".so", ".dylib", ".class", ".obj", ".o"]},
            {"name": _t("ext_cat_archives"), "exts": [".zip", ".tar", ".gz", ".rar", ".7z"]},
            {"name": _t("ext_cat_temp_logs"), "exts": [".log", ".bak", ".tmp", ".pyc", ".pyo"]}
        ]

        current_exts = [e.strip().lower() for e in self.exclude_extensions_var.get().split(',') if e.strip()]
        current_exts = [('.' + e) if not e.startswith('.') else e for e in current_exts]

        # 既存のウィジェットをクリア
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.cb_widgets.clear()
        self.cat_vars.clear()
        self.ext_vars.clear()

        for cat in self.ext_categories:
            cat_name = cat["name"]
            cat_exts = cat["exts"]

            # カテゴリ親フレーム
            cat_frame = tk.Frame(self.scrollable_frame)
            cat_frame.pack(fill=tk.X, anchor="w", pady=(5, 5))

            # カテゴリ変数
            cat_var = tk.BooleanVar(value=False)
            self.cat_vars[cat_name] = cat_var

            cat_cb = tk.Checkbutton(
                cat_frame,
                text=cat_name,
                variable=cat_var,
                font=("TkDefaultFont", 10, "bold"),
                cursor="hand2",
                relief="flat",
                command=lambda name=cat_name: self._on_category_click(name)
            )
            cat_cb.pack(anchor="w")
            self.cb_widgets.append(cat_cb)

            # 拡張子フレーム (インデント)
            sub_frame = tk.Frame(cat_frame)
            sub_frame.pack(fill=tk.X, anchor="w", padx=20)

            for ext in cat_exts:
                checked = ext in current_exts
                ext_var = tk.BooleanVar(value=checked)
                self.ext_vars[ext] = ext_var

                ext_cb = tk.Checkbutton(
                    sub_frame,
                    text=ext,
                    variable=ext_var,
                    font=("TkDefaultFont", 9),
                    cursor="hand2",
                    relief="flat",
                    command=self._on_extension_click
                )
                ext_cb.pack(anchor="w", pady=2)
                self.cb_widgets.append(ext_cb)

            # カテゴリ変数の初期チェック設定
            checked_count = sum(1 for e in cat_exts if e in current_exts)
            cat_var.set(checked_count == len(cat_exts))

    def _on_category_click(self, cat_name: str) -> None:
        """カテゴリ一括チェッククリック時の動作"""
        target_cat = next((c for c in self.ext_categories if c["name"] == cat_name), None)
        if not target_cat:
            return

        is_checked = self.cat_vars[cat_name].get()
        cat_exts = target_cat["exts"]

        current_exts = [e.strip().lower() for e in self.exclude_extensions_var.get().split(',') if e.strip()]
        current_exts = [('.' + e) if not e.startswith('.') else e for e in current_exts]

        if is_checked:
            for ext in cat_exts:
                if ext not in current_exts:
                    current_exts.append(ext)
        else:
            for ext in cat_exts:
                if ext in current_exts:
                    current_exts.remove(ext)

        self.exclude_extensions_var.set(",".join(current_exts))

    def _on_extension_click(self) -> None:
        """個別の拡張子チェッククリック時の動作"""
        current_exts = []
        for ext, var in self.ext_vars.items():
            if var.get():
                current_exts.append(ext)
        self.exclude_extensions_var.set(",".join(current_exts))

    def _on_entry_changed(self, *args) -> None:
        """Entryの変更にチェックボタン状態を同期"""
        current_exts = [e.strip().lower() for e in self.exclude_extensions_var.get().split(',') if e.strip()]
        current_exts = [('.' + e) if not e.startswith('.') else e for e in current_exts]

        for ext, var in self.ext_vars.items():
            var.set(ext in current_exts)

        for cat in self.ext_categories:
            cat_name = cat["name"]
            cat_exts = cat["exts"]
            checked_count = sum(1 for e in cat_exts if e in current_exts)
            self.cat_vars[cat_name].set(checked_count == len(cat_exts))

    def _apply_cb_theme(self) -> None:
        """test.pyに基づき、ダーク/ライトテーマに合わせたチェックボタンの配色設定を行います。"""
        theme = self.theme_var.get()

        colors = {
            "dark": {
                "bg": "#2e2e2e",
                "fg": "#ffffff",
                "selectcolor": "#555555",
                "active_bg": "#3e3e3e",
                "active_fg": "#ffffff",
            },
            "light": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "selectcolor": "#ffffff",
                "active_bg": "#e0e0e0",
                "active_fg": "#000000",
            }
        }

        c = colors.get(theme, colors["light"])

        # キャンバスやスクロールフレームの背景も同期
        self.canvas.config(bg=c["bg"])
        self.scrollable_frame.config(bg=c["bg"])

        # すべてのカテゴリ・子フレームおよびCheckbutton의 配色適用
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.config(bg=c["bg"])
                for sub_w in widget.winfo_children():
                    if isinstance(sub_w, tk.Frame):
                        sub_w.config(bg=c["bg"])

        for cb in self.cb_widgets:
            cb.config(
                bg=c["bg"],
                fg=c["fg"],
                selectcolor=c["selectcolor"],
                activebackground=c["active_bg"],
                activeforeground=c["active_fg"]
            )

    def _on_language_changed(self) -> None:
        """言語の切り替えを検知した際、設定画面全体の表示テキストを即座に更新します。"""
        _t = self.app.translator

        # タイトル
        self.title(_t('settings'))

        # 各フレームとラベル
        self.appearance_frame.config(text=_t('theme'))
        self.theme_label.config(text=_t('theme') + ":")

        self.lang_frame.config(text=_t('language'))
        self.lang_label.config(text=_t('language') + ":")

        self.ext_frame.config(text=_t('exclude_extensions'))
        self.ext_label.config(text=_t('exclude_extensions') + ":")

        self.save_btn.config(text=_t('save'))
        self.cancel_btn.config(text=_t('cancel'))

        # チェックボックスリストの再構築 (カテゴリ名の翻訳が更新されます)
        self._populate_ext_list()

        # テーマ配色も再適用
        self._apply_cb_theme()

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
