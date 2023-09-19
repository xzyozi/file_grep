import os , datetime
import PySimpleGUI as sg
import subprocess
import logging
from rich.logging import RichHandler

#  +----- my py -------------------------------------+
import sec_f_grep_3

# debug ------------------------------------------------
# Create RichHandler and set it as a log handler

handler = RichHandler()
logging.disable(logging.CRITICAL)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s', handlers=[handler])


#  +--custom logging function ----------------------------
# def my_custom_logger(message:str) -> None:
#     custom_logger = logging.getLogger('custom_logger')
#     custom_logger.debug(f'My Custom Log: {message}')
# my_custom_logger('program begins.')


# +---------------------------------------------------------------
# + gui class 
# +---------------------------------------------------------------

class Find_text_gui():
    def __init__(self):
        self.right_click_menu_jp = ['&Right',['コピー', '貼り付け'] ]
        self.window = None
        self.init_window_main()
    
    def init_window_main(self) :
        self.layout = [
        [sg.Text("Enter Folder Path:")],
        [sg.InputText(key="-FOLDER_PATH-"), sg.FolderBrowse()],
        [sg.InputText(key="-SERACH_TEXT-",default_text="import", right_click_menu= self.right_click_menu_jp),sg.Text("grep text here")],
        [sg.Button("Read Folder"), sg.Button("Exit")],
        [sg.Text(size=(60, 10), key="-OUTPUT-")]
        ]

        self.window = sg.Window("Read Folder Contents", self.layout , finalize=True)# .Finalize()

    # made file name --------------------------------------------------
    def output_text_path_make(self, fd_text : str) -> str:
        now_time = datetime.datetime.now()
        #logging.debug(now_time)
        file_name = now_time.strftime("%Y%m%d_%H%M%S")
        file_name = file_name[2:]

        OUTPUT_TEXT_PATH = f"./{file_name}_{fd_text}_grep.txt"

        #os.environ['OUTPUT_TEXT_PATH'] = f'{file_name}_grep.txt'

        return OUTPUT_TEXT_PATH
    #-------------------------------------------------------------
    
    #--再帰的にフォルダーパスを分解してリストに保存する関数----------
    def split_path_into_folders(self, path : str) -> str:
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
    #-------------------------------------------------------------

    def open_text_editor(self, file_path : str) -> None:
        try:
            #subprocess.Popen(["notepad.exe", file_path])
            subprocess.Popen(["start", file_path], shell=True)
            #subprocess.Popen(f'start "" "{file_path}"', shell=True)
        except FileNotFoundError:
            print("not found file .")
    
    # Is the path right ----------------------------------------------

    def is_path_right(self, folder_path : str) -> bool:
        if os.path.isdir(folder_path):
            return True
        else:
            return False

    def is_valid_path(self, path : str) -> bool:
        if os.path.exists(path) and os.path.isabs(path):
            return True
        else:
            return False

    #-------------------------------------------------------------
    def main(self) -> None:
        
        while True:
            event, values = self.window.read()

            if event == sg.WINDOW_CLOSED or event == "Exit":
                break
            elif event == "Read Folder":
            
                folder_path = values["-FOLDER_PATH-"]
                #print(folder_path)
                folder_path = r"{}".format(folder_path)
                # folder_path = folder_path.replace("/","\ ")
                # folder_path = folder_path.replace(" ","")
                #print(folder_path)
                if self.is_valid_path(folder_path) :
                    
                    folder_path = self.split_path_into_folders(folder_path)
                    
                    #print(folder_path)
                    # folder_path = folder_path.encode('unicode_escape').decode('utf-8')
                    
                    #result = read_folder_contents(folder_path)
                    #print(result)
                    #window["-OUTPUT-"].update(result)
                    logging.debug(folder_path)

                    
                    
                    fd_text = values["-SERACH_TEXT-"]
                    self.window["-OUTPUT-"].update("")
                    #another file 
                    OUTPUT_TEXT_PATH = self.output_text_path_make(fd_text)

                    # print(fd_text,OUTPUT_TEXT_PATH)
                    
                    find_files_count = sec_f_grep_3.find_text_grep(folder_path, fd_text, OUTPUT_TEXT_PATH)
                    
                    # make text "if" mode
                    
                    if find_files_count > 0 :
                        self.window["-OUTPUT-"].update(f"{OUTPUT_TEXT_PATH} \nfinish")

                        self.open_text_editor(fr"./{OUTPUT_TEXT_PATH}")
                        #print(OUTPUT_TEXT_PATH,type(OUTPUT_TEXT_PATH))
                else :
                    sg.popup_error(f"{folder_path} is not a valid path.", auto_close=True)

        # Close the window
        self.window.close()

if __name__ == "__main__":
    gui = Find_text_gui()
    gui.main()
