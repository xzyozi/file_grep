import os 
import chardet

PATH = "./panel"

files = os.listdir(PATH)
count = 0
fd_file = []

FD_TEXT = "i2c_driver"   #探したいtext

#print(files)
for i in files:
    root,ext = os.path.splitext(i)
    if count > 0 : break  
    #print(root,type(root))
    #print(ext,type(ext))
    file_lst = [i]
    if ext == ".c":
        #print(f"{PATH}/{i}")
        with open(f"{PATH}/{i}", 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            #print(result)
            encoding = result['encoding']
            try:
                content = raw_data.decode(encoding)
                #print(content)
                #print(type(content))
                
                fd_flg = FD_TEXT in content
                if fd_flg == True :
                    output_string = " ".join(map(str, file_lst))
                    fd_file.append(output_string)
                #print(type(content))
            except UnicodeDecodeError:
                print(f"Error decoding file: {filename}")
            # lines_strip = [line.strip() for line in lines]
            # print(lines_strip)
        #count += 1
print(len(files))
print(fd_file)
print(len(fd_file)) 
try :
    with open('test.txt', 'w') as f:
        for file_name in fd_file:
            f.write(f"{file_name}\n")
except PermissionError : print("file may be open")
else: print("Generated textfile.")