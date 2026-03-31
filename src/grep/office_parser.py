from __future__ import annotations
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Optional

class OfficeParser:
    """
    Excel (.xlsx) や Word (.docx) ファイルからテキストを抽出するパーサ。
    標準ライブラリのみを使用します。
    """

    NAMESPACE = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        's': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    }

    @classmethod
    def get_docx_text(cls, file_path: str) -> List[str]:
        """Wordファイル (.docx) から段落ごとのテキストリストを抽出します。"""
        texts = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zp:
                with zp.open('word/document.xml') as f:
                    xml_content = f.read()
                    tree = ET.fromstring(xml_content)
                    # w:p (paragraph) 内の w:t (text) をすべて収集
                    for paragraph in tree.findall('.//w:p', cls.NAMESPACE):
                        parts = []
                        for t in paragraph.findall('.//w:t', cls.NAMESPACE):
                            if t.text:
                                parts.append(t.text)
                        if parts:
                            texts.append("".join(parts))
        except (zipfile.BadZipFile, KeyError, ET.ParseError):
            # ファイルが壊れている、または構造が異なる場合は空を返す
            pass
        return texts

    @classmethod
    def get_xlsx_text(cls, file_path: str) -> List[str]:
        """Excelファイル (.xlsx) の共有文字列(Shared Strings)からテキストリストを抽出します。"""
        texts = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zp:
                # Excelのメインテキストは通常 xl/sharedStrings.xml に集約されている
                if 'xl/sharedStrings.xml' in zp.namelist():
                    with zp.open('xl/sharedStrings.xml') as f:
                        xml_content = f.read()
                        tree = ET.fromstring(xml_content)
                        # si (string item) 内の t (text) を収集
                        for t in tree.findall('.//s:t', cls.NAMESPACE):
                            if t.text:
                                texts.append(t.text)
        except (zipfile.BadZipFile, KeyError, ET.ParseError):
            pass
        return texts

    @classmethod
    def extract_text(cls, file_path: str) -> Optional[List[str]]:
        """拡張子に応じて適切なテキスト抽出メソッドを呼び出します。"""
        ext = file_path.lower()
        if ext.endswith('.docx'):
            return cls.get_docx_text(file_path)
        elif ext.endswith('.xlsx'):
            return cls.get_xlsx_text(file_path)
        return None
