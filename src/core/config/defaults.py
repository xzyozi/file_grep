from __future__ import annotations

# UIの色設定 (ライトモード / ダークモード)
THEMES = {
    'light': {
        'bg': '#f0f0f0',
        'fg': '#000000',
        'frame_bg': '#ffffff',
        'label_fg': '#000000',
        'button_bg': '#e1e1e1',
        'button_fg': '#000000',
        'select_bg': '#0078d7',
        'select_fg': '#ffffff',
        'entry_bg': '#ffffff',
        'entry_fg': '#000000',
        'listbox_bg': '#ffffff',
        'listbox_fg': '#000000',
        'menu_bg': '#ffffff',
        'menu_fg': '#000000',
        'active_menu_bg': '#0078d7',
        'active_menu_fg': '#ffffff',
    },
    'dark': {
        'bg': '#2d2d2d',
        'fg': '#ffffff',
        'frame_bg': '#333333',
        'label_fg': '#e1e1e1',
        'button_bg': '#444444',
        'button_fg': '#ffffff',
        'select_bg': '#0078d7',
        'select_fg': '#ffffff',
        'entry_bg': '#1e1e1e',
        'entry_fg': '#ffffff',
        'listbox_bg': '#1e1e1e',
        'listbox_fg': '#ffffff',
        'menu_bg': '#333333',
        'menu_fg': '#ffffff',
        'active_menu_bg': '#0078d7',
        'active_menu_fg': '#ffffff',
    }
}

# ウィンドウの規定サイズ
MAIN_WINDOW_GEOMETRY = '1000x800'
SETTINGS_WINDOW_GEOMETRY = '600x400'

# ボタンパディングなどの定数
BUTTON_PADDING_X = 5
BUTTON_PADDING_Y = 5
FRAME_PADDING = 10
