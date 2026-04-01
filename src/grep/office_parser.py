from __future__ import annotations
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Optional

class OfficeParser:
    """
    Excel (.xlsx) や Word (.docx) ファイルからテキストを抽出するパーサ。
    標準ライブラリのみを使用します。

    【現在の注意点】
    1. Excel: 共有文字列 (sharedStrings.xml) のみを対象としています。
       数値セルや日付セル (ワークシートXML内の <v> タグ) は現在検索対象外です。
    2. Word: メイン文書 (document.xml) のみを対象としています。
       ヘッダー、フッター、テキストボックス内のテキストは現在検索対象外です。
    """

    NAMESPACE = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        's': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    }

    @classmethod
    def get_docx_text(cls, file_path: str) -> List[str]:
        """Wordファイル (.docx) からテキストを抽出します (iterparse版)。"""
        texts = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zp:
                with zp.open('word/document.xml') as f:
                    # 段落(w:p)ごとにテキストを集約
                    current_paragraph_parts = []
                    context = ET.iterparse(f, events=('start', 'end'))
                    
                    ns_w = f"{{{cls.NAMESPACE['w']}}}"
                    tag_p = f"{ns_w}p"
                    tag_t = f"{ns_w}t"

                    for event, elem in context:
                        if event == 'end' and elem.tag == tag_t:
                            if elem.text:
                                current_paragraph_parts.append(elem.text)
                        
                        elif event == 'end' and elem.tag == tag_p:
                            if current_paragraph_parts:
                                texts.append("".join(current_paragraph_parts))
                                current_paragraph_parts = []
                            # メモリ節約のため処理済み要素をクリア
                            elem.clear()
        except (zipfile.BadZipFile, KeyError, ET.ParseError):
            pass
        return texts

    @classmethod
    def get_xlsx_text(cls, file_path: str) -> List[str]:
        """Excelファイル (.xlsx) の共有文字列からテキストを抽出します (iterparse版)。"""
        texts = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zp:
                if 'xl/sharedStrings.xml' in zp.namelist():
                    with zp.open('xl/sharedStrings.xml') as f:
                        context = ET.iterparse(f, events=('end',))
                        tag_t = f"{{{cls.NAMESPACE['s']}}}t"

                        for event, elem in context:
                            if elem.tag == tag_t and elem.text:
                                texts.append(elem.text)
                            elem.clear()
        except (zipfile.BadZipFile, KeyError, ET.ParseError):
            pass
        return texts

    @classmethod
    def extract_text(cls, file_path: str) -> List[str]:
        """拡張子に応じて適切な抽出メソッドを呼び出します。不明な場合は空リストを返します。"""
        ext = file_path.lower()
        if ext.endswith(('.docx', '.docm')):
            return cls.get_docx_text(file_path)
        elif ext.endswith(('.xlsx', '.xlsm')):
            return cls.get_xlsx_text(file_path)
        return []
