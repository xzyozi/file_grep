import os
import datetime
import wx
import subprocess
import logging
from rich.logging import RichHandler

# +----- my py -------------------------------------+
import sec_f_grep_3

# debug ------------------------------------------------
# Create RichHandler and set it as a log handler

handler = RichHandler()
logging.disable(logging.CRITICAL)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s', handlers=[handler])

# +--custom logging function ----------------------------
# def my_custom_logger(message:str) -> None:
#     custom_logger = logging.getLogger('custom_logger')
#     custom_logger.debug(f'My Custom Log: {message}')
# my_custom_logger('program begins.')

# +---------------------------------------------------------------
# + gui class
# +---------------------------------------------------------------

class FindTextGUI(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Read Folder Contents", size=(400, 200))
        self.panel = wx.Panel(self)
        self.right_click_menu_jp = wx.Menu()
        self.right_click_menu_jp.Append(wx.ID_COPY, "コピー")
        self.right_click_menu_jp.Append(wx.ID_PASTE, "貼り付け")
        self.init_window_main()
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def init_window_main(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)

        folder_label = wx.StaticText(self.panel, label="Enter Folder Path:")
        self.folder_path = wx.TextCtrl(self.panel)
        folder_browse_btn = wx.Button(self.panel, label="Browse")
        self.Bind(wx.EVT_BUTTON, self.on_browse, folder_browse_btn)
        hbox1.Add(folder_label, flag=wx.RIGHT, border=8)
        hbox1.Add(self.folder_path, proportion=1)
        hbox1.Add(folder_browse_btn, flag=wx.LEFT, border=8)

        search_label = wx.StaticText(self.panel, label="grep text here")
        self.search_text = wx.TextCtrl(self.panel, value="import")
        hbox2.Add(search_label, flag=wx.RIGHT, border=8)
        hbox2.Add(self.search_text, proportion=1)
        
        process_btn = wx.Button(self.panel, label="Process")
        self.Bind(wx.EVT_BUTTON, self.on_read_folder, process_btn)

        regex_checkbox = wx.CheckBox(self.panel, label="Enable Regular Expression")
        self.output_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(300, 100))
        self.output_text.SetLabel("")
        hbox3.Add(regex_checkbox)
        hbox3.Add(self.output_text, proportion=1, flag=wx.TOP | wx.EXPAND)

        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        vbox.Add(hbox2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        vbox.Add(process_btn, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(hbox3, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.panel.SetSizer(vbox)
        self.Show()

    def output_text_path_make(self, fd_text: str) -> str:
        now_time = datetime.datetime.now()
        file_name = now_time.strftime("%Y%m%d_%H%M%S")
        file_name = file_name[2:]
        OUTPUT_TEXT_PATH = f"./{file_name}_{fd_text}_grep.txt"
        return OUTPUT_TEXT_PATH

    def open_text_editor(self, file_path: str) -> None:
        try:
            subprocess.Popen(["start", file_path], shell=True)
        except FileNotFoundError:
            print("not found file .")

    def is_path_right(self, folder_path: str) -> bool:
        if os.path.isdir(folder_path):
            return True
        else:
            return False

    def is_valid_path(self, path: str) -> bool:
        if os.path.exists(path) and os.path.isabs(path):
            return True
        else:
            return False

    def split_path_into_folders(self, path: str) -> str:
        folders = []
        while True:
            path, folder = os.path.split(path)
            if folder:
                folders.append(folder)
            else:
                if path:
                    folders.append(path)
                break
        folders.reverse()
        result_path = os.path.join(*folders)
        return result_path

    def on_browse(self, event):
        dialog = wx.DirDialog(self, "Choose a directory:")
        if dialog.ShowModal() == wx.ID_OK:
            self.folder_path.SetValue(dialog.GetPath())
        dialog.Destroy()

    def get_checkbox_re_value(self, event):
        regex_enabled = self.regex_checkbox.GetValue()
        return regex_enabled

    def on_read_folder(self, event):
        folder_path = self.folder_path.GetValue()
        folder_path = fr"{folder_path}"
        if self.is_valid_path(folder_path):
            folder_path = self.split_path_into_folders(folder_path)
            fd_text = self.search_text.GetValue()
            self.output_text.SetLabel("")
            regex_enabled = self.get_checkbox_re_value()
            if regex_enabled:
                fd_text = r"\b{}\b".format(fd_text)
            OUTPUT_TEXT_PATH = self.output_text_path_make(fd_text)
            find_files_count = sec_f_grep_3.find_text_grep(folder_path, fd_text, OUTPUT_TEXT_PATH)
            if find_files_count > 0:
                self.output_text.SetLabel(f"{OUTPUT_TEXT_PATH} \nfinish")
                self.open_text_editor(fr"./{OUTPUT_TEXT_PATH}")
        else:
            wx.LogError(f"{folder_path} is not a valid path.")

    def on_close(self, event):
        self.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    gui = FindTextGUI()
    app.MainLoop()
