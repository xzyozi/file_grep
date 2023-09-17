import os 
from rich import print

#PATH = ".\sample"
#PATH = ".\meta-pew-baseboard"
PATH = r"C:/Users\t_sai\OneDrive\デスクトップ\python\jikkou"
PATH = r"C:\Users\xzyoi\Desktop\jikkou"



print(PATH)
for root, dirs, files in os.walk(PATH):
    # for file in files:
    #     root, ext = os.path.splitext(file)
    print("path -- :",root)
    print("dirs -- :",dirs)
    print("files --:",files)
    print("- "*10)