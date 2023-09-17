import os 
import chardet
import logging
import datetime

#debug
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logging.disable(logging.CRITICAL)

logging.debug('program begins.')

#PATH = "./sample"
#PATH = "./panel"
PATH = ".\meta-pew-baseboard"
PATH = r"C:\Users\t_sai\OneDrive\デスクトップ\python\jikkou"

now_time = datetime.datetime.now()
#logging.debug(now_time)
file_name = now_time.strftime("%Y%m%d%H%M%S")
file_name = file_name[2:]

OUTPUT_TEXT_PATH = f"{file_name}_grep.txt"

os.environ['OUTPUT_TEXT_PATH'] = f'{file_name}_grep.txt'

#files = os.listdir(PATH)
count = 0
fd_file = []

FD_TEXT = "i2c_"   #探したいtext
FD_TEXT = "gui"
#階層ごとにfilenameの前につけるようなこーどがいる
def find_text_srch(filename,path,FD_TEXT):
    #print(filename)
    logging.debug(filename)
    root,ext = os.path.splitext(filename)
    #if count > 0 : break  
    #print(root,type(root))
    #print(ext,type(ext))
    file_lst = [filename]

    #実行ファイル直下で実行すると生成したtextファイルも引っかかるので除外
    if filename[-8:] == "grep.txt":
        return 0

    #print(f"{PATH}/{i}")

#以下のコードも対応できるものにしなくてはならない
#----------------↓↓↓--------------------------------------
    with open(f"{path}\{filename}", 'rb') as f:
#---------------------------------------------------------        
        
        raw_data = f.read()
        result = chardet.detect(raw_data)
        #print(result)
        encoding = result['encoding']
        try:
            content = raw_data.decode(encoding)
        except:return 0
        
        # try:
        
        #print(content)
        #print(type(content))
        lines = content.splitlines()
        #print(lines)
        matched_lines,fst_cnt = [],0
        for line_num, text_line in enumerate(lines, start=1):
            fd_flg = FD_TEXT in text_line
            if fd_flg == True :
                if fst_cnt == 0:
                    with open(OUTPUT_TEXT_PATH, 'a') as f:
                    
                        f.write(f"textfile name : {path}\{filename}\n")
                        fst_cnt += 1
                        try :
                            f.write(f"  line{line_num} : {text_line} \n")
                        except :return 0
                        
                else :
                    with open(OUTPUT_TEXT_PATH, 'a') as f:
                    
                        f.write(f"  line{line_num} : {text_line} \n")
                    
                    
                    
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
    return bool(fst_cnt == 1)

#print(files)
#for filename in files:
def find_text_grep(PATH,FD_TEXT):
    now_time = datetime.datetime.now()
    #logging.debug(now_time)
    file_name = now_time.strftime("%Y%m%d%H%M%S")
    file_name = file_name[2:]

    OUTPUT_TEXT_PATH = f"{file_name}_grep.txt"

    os.environ['OUTPUT_TEXT_PATH'] = f'{file_name}_grep.txt'
    
    
    for path, _, files in os.walk(PATH):
        
        # if find_text_srch(filename,path,FD_TEXT) == True: count+=1
        # else: pass
        for filename in files:
            find_text_srch(filename,path,FD_TEXT)
    

    else: 
        if count == 0:
            print("Not textfile")
        else :print("Generated textfile.")

if "__main__" == __name__:
    find_text_grep(PATH,FD_TEXT)