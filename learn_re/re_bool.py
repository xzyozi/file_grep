import re

# input_text = input(">>")

input_text = r"\d"

text = """
123
dge

"""

print(bool(re.search(re.compile(fr"{input_text}"), text)))