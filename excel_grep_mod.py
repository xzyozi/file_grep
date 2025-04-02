import pandas as pd
"""
pip install openpyxl is required because openpyxl is used in pandas
"""
import chardet  # 文字コード検出ライブラリ
import re

output_file = ""

def excel_grep(filename, path, search_term, output_file, write_line_text=True):

    # Excelファイルを読み込み
    file_path = f"{path}/{filename}"
    try:
        df = pd.read_excel(file_path, sheet_name=None, header=None)
    except Exception as e:
        print(f"Error reading Excel file {filename}: {e}")
        return 0

    # 検索結果を格納するリスト
    results = []

    # シートごとに検索
    for sheet_name, sheet_df in df.items():
        for col_index, column in enumerate(sheet_df.columns):
            for index, cell_value in enumerate(sheet_df[column]):
                if isinstance(cell_value, str) and pd.notna(cell_value) and search_term in cell_value:
                    # 一致した場合、情報をリストに追加
                    result_info = f'  Sheet: {sheet_name}, Cell: {chr(col_index + 65)}{index + 1}, Value: {cell_value}'
                    results.append(result_info)

    # print(results)
    # 検索結果をファイルに書き込む
    with open(output_file, 'a', encoding='utf-8') as output:
        if results:
            # Change the file path to activate the link.
            path = path.replace("/", "\ ")
            path = path.replace(" ", "")
            filename = filename.replace("/", "\ ")
            filename = filename.replace(" ", "")
            filename_line = fr"find file : {path}\{filename}  -----"
            output.write(f"{filename_line}\n")

            # line write
            if write_line_text:
                for write_line in results:
                    try:
                        output.write(f"{write_line}\n")
                    except Exception as e:
                        print(f"Error writing line to output file: {e}")
                output.write("\n")

            return 1  
        else:
            return 0




if __name__ == "__main__":
    # 使用例
    excel_grep(r"file_example_XLSX_10.xlsx", r"C:\Users\xzyoi\Downloads" ,"Male" , output_file)
