import os

path = "/path/to/your/file_or_directory"
base_name = os.path.basename(path)

if os.path.isfile(path):
    file_name = base_name
    dir_name = os.path.dirname(path)
else:
    file_name = None
    dir_name = base_name

print("ファイル名:", file_name)
print("ディレクトリ名:", dir_name)
