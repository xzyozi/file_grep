import os , threading
import chardet
import logging
import datetime
from rich.logging import RichHandler
from rich import print

# Create RichHandler and set it as a log handler
handler = RichHandler()
# debug logging functions --------------------------------------------------
def logging_function() -> None:
    # Create RichHandler and set it as a log handler
    handler = RichHandler()
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s', handlers=[handler])
    # logging.disable(logging.CRITICAL)

    logging.debug('program begins.')

# --------------------------------------------------------------------------

output_file_lock = threading.Lock()

thread_results = []

#PATH = "./sample"
#PATH = "./panel"
PATH = r".\meta-pew-baseboard"
#PATH = r"C:\Users\t_sai\OneDrive\デスクトップ\python\jikkou"
#PATH = r"C:\Users\t_sai\OneDrive\デスクトップ\python\zatta\新しいフォルダー (2)\forxai"


# now_time = datetime.datetime.now()
# #logging.debug(now_time)
# file_name = now_time.strftime("%Y%m%d%H%M%S")
# file_name = file_name[2:]

# OUTPUT_TEXT_PATH = f"{file_name}_grep.txt"

# os.environ['OUTPUT_TEXT_PATH'] = f'{file_name}_grep.txt'

#files = os.listdir(PATH)
count = 0
fd_file = []

FD_TEXT = "i2c_"   #探したいtext
FD_TEXT = "gui"
# FD_TEXT = "tracker"


#file name --------------------------------------------------
def output_text_path_make() -> str:
    now_time = datetime.datetime.now()
    #logging.debug(now_time)
    file_name = now_time.strftime("%Y%m%d_%H%M%S")
    file_name = file_name[2:]

    OUTPUT_TEXT_PATH = f"{file_name}_grep.txt"

    os.environ['OUTPUT_TEXT_PATH'] = f'{file_name}_grep.txt'

    return OUTPUT_TEXT_PATH
#-------------------------------------------------------------

# thread mode function -----------------------------------------------
def fd_text_serch(lines : list, FD_TEXT : str, start : int) -> list:
    result_box = []
    for line_num, text_line in enumerate(lines, start):
        if FD_TEXT in text_line :
            insert_text = f"  line{line_num} : {text_line} "
            result_box.append(insert_text)
    
    return result_box



def process_files_in_directory(path, text_to_find, OUTPUT_TEXT_PATH) -> None:
    count = 0
    for filename in os.listdir(path):
        # print(f"-------------------------------{filename}")
        if os.path.isfile(os.path.join(path, filename)):
            count += find_text_srch(filename, path, text_to_find, OUTPUT_TEXT_PATH)
    
    # Append the result to the global list
    thread_results.append(count)

# ----------------------------------------------------------------

# find text --------------------------------------------------
def find_text_srch(filename, path, FD_TEXT, OUTPUT_TEXT_PATH, write_line_text :bool= True) -> int :
    # print(filename)
    logging.debug(filename)
    root,ext = os.path.splitext(filename)
    #if count > 0 : break  
    #print(root,type(root))
    #print(ext,type(ext))
    #file_lst = [filename]

    binary_file_extensions = [
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".ico",
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        
        ".pyc",  # Pythonコンパイル済みバイトコード
        ".pyo",  # Pythonコンパイル済みバイトコード (最適化)
        
        ".o",
        ".obj",

        # バイトコード
        ".class",  # Javaバイトコード
        
        # インタプリタ関連
        ".dll",    # ダイナミックリンクライブラリ (C/C++など)
        ".so",     # 共有ライブラリ (Linux)
        ".dylib",  # ダイナミックライブラリ (macOS)
        
        # 実行可能ファイル
        ".exe",    # 実行可能ファイル (Windows)
        
        # その他
        ".bin",    # バイナリデータファイル

        ".pack",
        ".idx"
    ]

    if ext in binary_file_extensions :
        # print(filename)
        return 0

    #実行ファイル直下で実行すると生成したtextファイルも引っかかるので除外
    if filename[-8:] == "grep.txt":
        return 0

    #print(f"{PATH}/{i}")

    #以下のコードも対応できるものにしなくてはならない
    #-------------↓↓↓-----------------------------------------
    with open(f"{path}\{filename}", 'rb') as f:
    #---------------------------------------------------------        
        
        raw_data = f.read()
        result = chardet.detect(raw_data)
        # print(result)
        encoding = result['encoding']
        
        if encoding == None: 
            print(filename)
            return 0
        
        try:
            content = raw_data.decode(encoding)
        except Exception as e:
            print(f"{filename} is {e}")
            return 0
        
        # try:
        
        #print(content)
        #print(type(content))
        lines = content.splitlines()
        #print(lines)
        half_lines_len = len(lines)//2

        matched_lines,fst_cnt = [], 0
        

        pre_slice = lines[:half_lines_len]
        end_slice = lines[half_lines_len:]

        # for line_num, text_line in enumerate(lines, start=1):
        #     fd_flg = FD_TEXT in text_line
        #     if fd_flg == True :
        #         if fst_cnt == 0:
        #             with open(OUTPUT_TEXT_PATH, 'a') as f:
                    
        #                 f.write(f"textfile name : {path}\{filename}\n")
        #                 fst_cnt += 1
        #                 try :
        #                     f.write(f"  line{line_num} : {text_line} \n")
        #                 except :return 0
                        
        #         else :
        #             with open(OUTPUT_TEXT_PATH, 'a') as f:
                    
        #                 f.write(f"  line{line_num} : {text_line} \n")
        
        pre_box, end_box = [], []

        pre_thread = threading.Thread(target= lambda:pre_box.extend( fd_text_serch(pre_slice,FD_TEXT,start=1)) )
        end_thread = threading.Thread(target= lambda:end_box.extend( fd_text_serch(end_slice,FD_TEXT,start=half_lines_len + 1)) )

        pre_thread.start()
        end_thread.start()

        pre_thread.join()
        end_thread.join()

        result_box = pre_box + end_box
        #print(result_box)
        match_file = 0
        #gui
        if pre_box != [] or end_box != []:
            match_file += 1

            # Change the file path to activate the link.

            path = path.replace("/","\ ")
            path = path.replace(" ","")
            # path = path.replace("(", r"\(").replace(")", r"\)")

            filename = filename.replace("/","\ ")
            filename = filename.replace(" ", "")
            # filename = filename.replace("(", r"\(").replace(")", r"\)")


            filename_line = fr"file name : {path}\{filename}  -----"
            with output_file_lock:  # Acquire the lock before writing to the output file
                with open(OUTPUT_TEXT_PATH, 'a') as f:
                    f.write(f"{filename_line}\n")
                    
                    # line write-----------------------------
                    if write_line_text == False : pass
                    else :
                        for write_line in result_box :
                            try :
                                f.write(f"{write_line}\n")        
                            except Exception as e :
                                print(f"error code : {e}")
                        else : 
                            f.write(f"\n") 

                    # ---------------------------------------
                    
                    #output_string = " ".join(map(str, file_lst))
                    #fd_file.append(output_string)

                    #matched_lines.append(line_num)
            # if matched_lines != []:
            #     try :
            #         with open('test_2.txt', 'a') as f:
            #             write_text = f"{i} {matched_lines}"
            #             f.write(f"{write_text}\n")
            #             count += 1
            #     except PermissionError : print("file may be open")                    


        # except UnicodeDecodeError:
        #     logging.debug(f"Error decoding file: {filename}")

        # lines_strip = [line.strip() for line in lines]
        # print(lines_strip)
    
    #logging.debug(bool(fst_cnt == 1))
    #return bool(fst_cnt == 1)
    return match_file
# --------------------------------------------------------------


#print(files)
#for filename in files:
def find_text_grep(PATH, FD_TEXT, OUTPUT_TEXT_PATH) -> int :
    # logging_function()
    count = 0
    now1 = datetime.datetime.now()

    # output_file_lock = threading.Lock()

    # thread_results = []
    
    # for path, _, files in os.walk(PATH):
        
        

        # if find_text_srch(filename,path,FD_TEXT) == True: count+=1
        # else: pass
        # for filename in files:
        #     count += \
        #     find_text_srch(filename, path, FD_TEXT, OUTPUT_TEXT_PATH)

    threads = []
    for root, dirs, _ in os.walk(PATH):
        for directory in dirs:
            full_path = os.path.join(root, directory)
            
            # Replace backslashes with forward slashes and remove trailing spaces
            full_path = full_path.replace("\\", "/").strip()
            

            thread = threading.Thread(target=process_files_in_directory, args=(full_path, FD_TEXT, OUTPUT_TEXT_PATH))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    count = sum(thread_results)


    
    
    
    if count == 0:
        print("Not textfile")
    else :print("Generated textfile.")
    
    now2 = datetime.datetime.now()
    print(now2 - now1)
    return count

if "__main__" == __name__:
    now1 = datetime.datetime.now()
    OUTPUT_TEXT_PATH = output_text_path_make()
    find_text_grep(PATH,FD_TEXT,OUTPUT_TEXT_PATH)

    now2 = datetime.datetime.now()
    print(now2 - now1)
    