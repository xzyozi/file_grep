import os
import datetime
import wx
import subprocess
import logging
from rich.logging import RichHandler

# +----- my py -------------------------------------+
import sec_f_grep_5

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
        # Initialize the GUI frame.
        super().__init__(None, title="Read Folder Contents", size=(400, 400))

        self.menu_panel = wx.Panel(self)
        self.panel = wx.Panel(self)

        # Initialize the main window of the GUI.
        self.init_menu_bar()
        # self.init_window_main()

        # size of the panel & menu bar
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.menu_panel, 0, flag=wx.EXPAND)
        main_panel = self.init_window_main()
        self.sizer.Add(main_panel, 1, flag=wx.EXPAND)
        self.SetSizerAndFit(self.sizer)
        
        # Bind the close event to the on_close method.
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Show() 

    def init_menu_bar(self):
        # Create a menu bar.
        menu_bar = wx.MenuBar()

        # Create a "File" menu.
        file_menu = wx.Menu()

        # Add a "Exit" menu item to the "File" menu.
        exit_item = file_menu.Append(wx.ID_EXIT, "Exit", "Exit the program")

        # Bind the "Exit" menu item to the on_exit method.
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)

        # Add the "File" menu to the menu bar.
        menu_bar.Append(file_menu, "File")

        # Set the menu bar for the frame.
        self.SetMenuBar(menu_bar)

    def init_window_main(self):
        # Create a vertical box sizer to arrange elements vertically.
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Create horizontal box sizers to arrange elements horizontally.
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)

        # Create a label for the folder path input.
        folder_label = wx.StaticText(self.panel, label="Enter Folder Path:")

        # Create a text input control for entering the folder path.
        self.folder_path = wx.TextCtrl(self.panel)

        # Create a "Browse" button.
        folder_browse_btn = wx.Button(self.panel, label="Browse")

        # Bind the "Browse" button to the on_browse method.
        self.Bind(wx.EVT_BUTTON, self.on_browse, folder_browse_btn)

        # Add the folder path label, input control, and "Browse" button to hbox1.
        hbox1.Add(folder_label, flag=wx.RIGHT, border=8)
        hbox1.Add(self.folder_path, proportion=1)
        hbox1.Add(folder_browse_btn, flag=wx.LEFT, border=8)

        # Create a label for the search text input.
        search_label = wx.StaticText(self.panel, label="grep text here")

        # Create a text input control for entering the search text.
        self.search_text = wx.TextCtrl(self.panel, value="import")

        # Add the search label and input control to hbox2.
        hbox2.Add(search_label, flag=wx.RIGHT, border=8)
        hbox2.Add(self.search_text, proportion=1)

        # Create a "Process" button.
        process_btn = wx.Button(self.panel, label="Process")

        # Bind the "Process" button to the on_read_folder method.
        self.Bind(wx.EVT_BUTTON, self.on_read_folder, process_btn)

        # Create a checkbox 
        self.regex_checkbox     = wx.CheckBox(self.panel, label="Enable Regular Expression")
        self.writeLine_checkbox = wx.CheckBox(self.panel, label="Enable Write Line")
        self.writeLine_checkbox.SetValue(True)
        # Create a multi-line text control for displaying output.
        self.output_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(300, 100))
        self.output_text.SetLabel("")  # Set the initial label of the output text control to an empty string.

        # Add the checkbox and output text control to hbox3.
        hbox3.Add(self.regex_checkbox, flag= wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        hbox3.Add(self.writeLine_checkbox, flag= wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        hbox3.Add(self.output_text, proportion=1, flag=wx.TOP | wx.EXPAND)

        # Add the horizontal box sizers and other elements to the vertical box sizer.
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        vbox.Add(hbox2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        vbox.Add(process_btn, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        vbox.Add(hbox3, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Set the vertical box sizer as the sizer for the panel.
        self.panel.SetSizer(vbox)
        
        return self.panel


    def output_text_path_make(self, fd_text: str) -> str:
        now_time = datetime.datetime.now()
        file_name = now_time.strftime("%Y%m%d_%H%M%S")
        file_name = file_name[2:]
        OUTPUT_TEXT_PATH = fr"./output/{file_name}_{fd_text}_grep.txt"
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

    def on_read_folder(self, event):
        
        
        folder_path = self.folder_path.GetValue()
        folder_path = fr"{folder_path}"
        if self.is_valid_path(folder_path):
            folder_path = self.split_path_into_folders(folder_path)
            fd_text = self.search_text.GetValue()
            self.output_text.SetLabel("")
            
            # Checkbox to value
            write_line_text = self.writeLine_checkbox.GetValue()
            regex_mode = self.regex_checkbox.GetValue()
            
            if regex_mode :
                OUTPUT_TEXT_PATH = self.output_text_path_make("regex")
            else :OUTPUT_TEXT_PATH = self.output_text_path_make(fd_text)
            
            find_files_count = sec_f_grep_5.find_text_grep(folder_path, fd_text, OUTPUT_TEXT_PATH, write_line_text, regex_mode)
            
            if find_files_count > 0:
                self.output_text.SetLabel(f"{OUTPUT_TEXT_PATH} \n finshed ")
                self.open_text_editor(fr"./{OUTPUT_TEXT_PATH}")
        else:
            wx.LogError(f"{folder_path} is not a valid path.")


    def on_exit(self, event):
        self.Close()

    def on_close(self, event):
        self.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    gui = FindTextGUI()
    app.MainLoop()
