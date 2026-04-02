from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class OfficeParser:
    """
    Excel (.xlsx) や Word (.docx) ファイルから、位置情報付きでテキストを抽出するパーサ。
    """

    NAMESPACE = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        's': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
    }

    @classmethod
    def _get_text_from_xml(cls, f) -> List[str]:
        """w:p, w:t 構造の XML からテキストを抽出するヘルパーメソッド。"""
        texts = []
        current_paragraph_parts = []
        try:
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
                    elem.clear()
        except ET.ParseError:
            pass
        return texts

    @classmethod
    def get_docx_content(cls, file_path: str) -> List[Dict[str, Any]]:
        """Wordファイルから本文・ヘッダー・フッターを抽出します。"""
        results = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zp:
                # 走査対象のXMLリストを取得 (本文、ヘッダー、フッター)
                xml_files = [n for n in zp.namelist() if n.startswith('word/') and n.endswith('.xml')]
                
                for xml_name in xml_files:
                    # 分類ラベルの作成
                    label = "Body"
                    if "header" in xml_name: label = "Header"
                    elif "footer" in xml_name: label = "Footer"
                    elif xml_name == "word/document.xml": label = "Body"
                    else: continue # その他(settings等)はスキップ

                    with zp.open(xml_name) as f:
                        lines = cls._get_text_from_xml(f)
                        for i, text in enumerate(lines, 1):
                            results.append({
                                "text": text,
                                "location": f"{label} P.{i}",
                                "metadata": {"xml": xml_name, "type": label}
                            })
        except Exception as e:
            logger.error(f"Error parsing DOCX {file_path}: {e}")
        return results

    @classmethod
    def get_xlsx_content(cls, file_path: str) -> List[Dict[str, Any]]:
        """Excelファイルからシート名・セル番地付きでテキストを抽出します。"""
        results = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zp:
                # 1. 共有文字列のロード
                shared_strings = []
                if 'xl/sharedStrings.xml' in zp.namelist():
                    with zp.open('xl/sharedStrings.xml') as f:
                        context = ET.iterparse(f, events=('end',))
                        tag_t = f"{{{cls.NAMESPACE['s']}}}t"
                        for _, elem in context:
                            if elem.tag == tag_t:
                                shared_strings.append(elem.text if elem.text else "")
                            elem.clear()

                # 2. シートIDとシート名のマッピング取得 (workbook.xml)
                sheet_id_to_name = {}
                with zp.open('xl/workbook.xml') as f:
                    root = ET.fromstring(f.read())
                    for sheet in root.findall('.//s:sheet', cls.NAMESPACE):
                        s_id = sheet.get(f"{{{cls.NAMESPACE['r']}}}id")
                        s_name = sheet.get('name')
                        if s_id and s_name:
                            sheet_id_to_name[s_id] = s_name

                # 3. シートIDとファイルパスのマッピング取得 (xl/_rels/workbook.xml.rels)
                rel_to_path = {}
                with zp.open('xl/_rels/workbook.xml.rels') as f:
                    root = ET.fromstring(f.read())
                    for rel in root.findall('.//rel:Relationship', cls.NAMESPACE):
                        r_id = rel.get('Id')
                        r_target = rel.get('Target')
                        if r_id and r_target:
                            # ターゲットパスを xl/ からの相対に調整
                            rel_to_path[r_id] = f"xl/{r_target}"

                # 4. 各ワークシートのパース
                tag_c = f"{{{cls.NAMESPACE['s']}}}c"
                tag_v = f"{{{cls.NAMESPACE['s']}}}v"
                
                for r_id, sheet_name in sheet_id_to_name.items():
                    xml_path = rel_to_path.get(r_id)
                    if not xml_path or xml_path not in zp.namelist():
                        continue
                    
                    with zp.open(xml_path) as f:
                        context = ET.iterparse(f, events=('start', 'end'))
                        current_cell_ref = ""
                        is_shared = False

                        for event, elem in context:
                            if event == 'start' and elem.tag == tag_c:
                                current_cell_ref = elem.get('r', '') # "A1" など
                                is_shared = (elem.get('t') == 's') # sharedStringか
                            
                            elif event == 'end' and elem.tag == tag_v:
                                value = elem.text
                                if value is not None:
                                    display_text = ""
                                    if is_shared:
                                        idx = int(value)
                                        display_text = shared_strings[idx] if 0 <= idx < len(shared_strings) else ""
                                    else:
                                        display_text = value # 数値等そのまま
                                    
                                    if display_text:
                                        results.append({
                                            "text": display_text,
                                            "location": f"{sheet_name}!{current_cell_ref}",
                                            "metadata": {"sheet": sheet_name, "cell": current_cell_ref}
                                        })
                            elif event == 'end' and elem.tag == tag_c:
                                elem.clear()

        except Exception as e:
            logger.error(f"Error parsing XLSX {file_path}: {e}")
        return results

    @classmethod
    def extract_content(cls, file_path: str) -> List[Dict[str, Any]]:
        """拡張子に応じてコンテンツを抽出します。"""
        ext = file_path.lower()
        if ext.endswith(('.docx', '.docm')):
            return cls.get_docx_content(file_path)
        elif ext.endswith(('.xlsx', '.xlsm')):
            return cls.get_xlsx_content(file_path)
        return []
