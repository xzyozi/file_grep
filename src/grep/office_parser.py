from __future__ import annotations

from dataclasses import dataclass
import io
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import unicodedata
import zipfile

try:
    import defusedxml.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


@dataclass
class EncodingResult:
    """エンコーディング検出結果"""
    encoding: str
    confidence: float
    detection_method: str
    has_bom: bool = False


@dataclass
class DecodedContent:
    """デコード済みコンテンツ"""
    text: str
    encoding_used: str
    success: bool
    has_replacement_chars: bool = False
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class EncodingManager:
    """多段階エンコーディング検出・管理クラス"""
    
    # 日本語・CJK文字対応のエンコーディング優先リスト
    DEFAULT_ENCODINGS = [
        'utf-8-sig',      # BOM付きUTF-8（最優先）
        'utf-8',          # 標準UTF-8
        'cp932',          # Windows日本語（Shift_JIS拡張）
        'shift_jis',      # 標準Shift_JIS
        'euc-jp',         # EUC-JP
        'iso-2022-jp',    # JIS
        'gb18030',        # 中国語
        'gbk',
        'gb2312',
        'big5',           # 繁体字中国語
        'euc-kr',         # 韓国語
        'cp949',          # 韓国語（拡張）
        'latin-1',        # 最後の手段
    ]
    
    def __init__(self, custom_encodings: Optional[List[str]] = None):
        self.encodings = custom_encodings or self.DEFAULT_ENCODINGS
    
    def detect_encoding(self, content: bytes) -> EncodingResult:
        """複数エンコーディングを段階的に試行し最適な文字コードを特定"""
        if not content:
            return EncodingResult("utf-8", 0.0, "empty_content")
        
        # BOM検出（最優先）
        bom_result = self._detect_bom(content)
        if bom_result.confidence > 0.9:
            return bom_result
        
        best_encoding = "utf-8"
        max_confidence = 0.0
        best_method = "fallback"
        
        for encoding in self.encodings:
            try:
                decoded_text = content.decode(encoding)
                confidence = self._calculate_confidence(decoded_text, encoding, content)
                
                if confidence > max_confidence:
                    max_confidence = confidence
                    best_encoding = encoding
                    best_method = "pattern_analysis"
                
                # 高信頼度での早期終了
                if confidence >= 0.95:
                    break
                    
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return EncodingResult(
            encoding=best_encoding,
            confidence=max_confidence,
            detection_method=best_method,
            has_bom=bom_result.has_bom
        )
    
    def _detect_bom(self, content: bytes) -> EncodingResult:
        """BOM（Byte Order Mark）の検出"""
        if content.startswith(b'\xef\xbb\xbf'):
            return EncodingResult("utf-8-sig", 1.0, "bom_detection", has_bom=True)
        if content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
            return EncodingResult("utf-16", 0.9, "bom_detection", has_bom=True)
        if content.startswith(b'\xff\xfe\x00\x00') or content.startswith(b'\x00\x00\xfe\xff'):
            return EncodingResult("utf-32", 0.9, "bom_detection", has_bom=True)
        return EncodingResult("utf-8", 0.0, "no_bom")
    
    def _calculate_confidence(self, text: str, encoding: str, original_bytes: bytes) -> float:
        """デコードされたテキストの信頼度を計算"""
        if not text:
            return 0.0
        
        confidence = 0.0
        
        # 1. 制御文字・置換文字の確認
        replacement_chars = text.count('')
        if replacement_chars > 0:
            confidence -= 0.3 * (replacement_chars / len(text))
        
        # 2. 日本語文字パターンの検出
        if encoding in ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis', 'euc-jp']:
            confidence += self._detect_japanese_patterns(text) * 0.4
        elif encoding in ['gb18030', 'gbk', 'gb2312', 'big5']:
            confidence += self._detect_chinese_patterns(text) * 0.4
        elif encoding in ['euc-kr', 'cp949']:
            confidence += self._detect_korean_patterns(text) * 0.4
        
        # ASCII互換性
        try:
            text.encode('ascii')
            confidence += 0.1
        except UnicodeEncodeError:
            pass
        
        # 文字の正規性
        try:
            normalized = unicodedata.normalize('NFC', text)
            if len(normalized) == len(text):
                confidence += 0.2
        except (ValueError, TypeError):
            confidence -= 0.1
        
        # バイト長とテキスト長の整合性
        try:
            re_encoded = text.encode(encoding)
            if len(re_encoded) == len(original_bytes):
                confidence += 0.2
        except (UnicodeEncodeError, UnicodeError):
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _detect_japanese_patterns(self, text: str) -> float:
        if not text:
            return 0.0
        japanese_chars = 0
        total_chars = len(text)
        for char in text:
            if '\u3040' <= char <= '\u309F': # ひらがな
                japanese_chars += 1
            elif '\u30A0' <= char <= '\u30FF': # カタカナ
                japanese_chars += 1
            elif '\u4E00' <= char <= '\u9FAF': # 漢字
                japanese_chars += 1
            elif '\uFF00' <= char <= '\uFFEF': # 全角記号
                japanese_chars += 0.5
        return japanese_chars / total_chars if total_chars > 0 else 0.0
    
    def _detect_chinese_patterns(self, text: str) -> float:
        if not text:
            return 0.0
        chinese_chars = 0
        total_chars = len(text)
        for char in text:
            if '\u4E00' <= char <= '\u9FAF' or '\uF900' <= char <= '\uFAFF':
                chinese_chars += 1
        return chinese_chars / total_chars if total_chars > 0 else 0.0
    
    def _detect_korean_patterns(self, text: str) -> float:
        if not text:
            return 0.0
        korean_chars = 0
        total_chars = len(text)
        for char in text:
            if '\uAC00' <= char <= '\uD7AF' or '\u1100' <= char <= '\u11FF':
                korean_chars += 1
        return korean_chars / total_chars if total_chars > 0 else 0.0
    
    def safe_decode(self, content: bytes, encoding: str = None) -> DecodedContent:
        """安全な文字列デコード"""
        if not content:
            return DecodedContent("", "utf-8", True)
        if encoding is None:
            encoding_result = self.detect_encoding(content)
            encoding = encoding_result.encoding
        
        try:
            decoded_text = content.decode(encoding)
            return DecodedContent(
                text=decoded_text,
                encoding_used=encoding,
                success=True,
                has_replacement_chars=('' in decoded_text)
            )
        except (UnicodeDecodeError, UnicodeError) as e:
            return self._decode_with_fallback(content, encoding, str(e))
    
    def _decode_with_fallback(self, content: bytes, failed_encoding: str, error_msg: str) -> DecodedContent:
        fallback_encodings = [enc for enc in self.encodings if enc != failed_encoding]
        for encoding in fallback_encodings:
            try:
                decoded_text = content.decode(encoding, errors='replace')
                return DecodedContent(
                    text=decoded_text,
                    encoding_used=encoding,
                    success=True,
                    has_replacement_chars=True,
                    errors=[f"Original encoding '{failed_encoding}' failed: {error_msg}"]
                )
            except (UnicodeDecodeError, UnicodeError):
                continue
        try:
            decoded_text = content.decode('utf-8', errors='replace')
            return DecodedContent(
                text=decoded_text,
                encoding_used='utf-8',
                success=False,
                has_replacement_chars=True,
                errors=[
                    f"All encodings failed. Used UTF-8 with replacement.",
                    f"Original error: {error_msg}"
                ]
            )
        except Exception as final_error:
            return DecodedContent(
                text="",
                encoding_used='utf-8',
                success=False,
                errors=[
                    f"Complete decoding failure: {final_error}",
                    f"Original error: {error_msg}"
                ]
            )


class OfficeParser:
    """
    Excel (.xlsx)・Word (.docx)・PowerPoint (.pptx) ファイルから、位置情報付きでテキストを抽出するパーサ。
    """
    encoding_manager = EncodingManager()

    NAMESPACE = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }

    @classmethod
    def _get_text_from_xml(cls, f: Any) -> List[str]:
        """w:p, w:t 構造の XML からテキストを抽出するヘルパーメソッド。"""
        texts = []
        current_paragraph_parts = []
        try:
            content = f.read()
            decoded = cls.encoding_manager.safe_decode(content)
            bytes_stream = io.BytesIO(decoded.text.encode('utf-8'))
            
            context = ET.iterparse(bytes_stream, events=("start", "end"))
            ns_w = f"{{{cls.NAMESPACE['w']}}}"
            tag_p = f"{ns_w}p"
            tag_t = f"{ns_w}t"

            for event, elem in context:
                if event == "end" and elem.tag == tag_t:
                    if elem.text:
                        current_paragraph_parts.append(elem.text)
                elif event == "end" and elem.tag == tag_p:
                    if current_paragraph_parts:
                        texts.append("".join(current_paragraph_parts))
                        current_paragraph_parts = []
                    elem.clear()
        except Exception:
            pass
        return texts

    @classmethod
    def get_docx_content(
        cls, file_path: str, on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> List[Dict[str, Any]]:
        """Wordファイルから本文・ヘッダー・フッターを抽出します。"""
        results = []
        try:
            with zipfile.ZipFile(file_path, "r") as zp:
                # 走査対象のXMLリストを取得 (本文、ヘッダー、フッター)
                xml_files = [n for n in zp.namelist() if n.startswith("word/") and n.endswith(".xml")]

                for xml_name in xml_files:
                    # 分類ラベルの作成
                    label = "Body"
                    if "header" in xml_name:
                        label = "Header"
                    elif "footer" in xml_name:
                        label = "Footer"
                    elif xml_name == "word/document.xml":
                        label = "Body"
                    else:
                        continue  # その他(settings等)はスキップ

                    with zp.open(xml_name) as f:
                        lines = cls._get_text_from_xml(f)
                        for i, text in enumerate(lines, 1):
                            results.append(
                                {
                                    "text": text,
                                    "location": f"{label} P.{i}",
                                    "metadata": {"xml": xml_name, "type": label},
                                }
                            )
        except Exception as e:
            if on_error:
                on_error(f"Error parsing DOCX {file_path}", e)
        return results

    @classmethod
    def get_sheet_summary(cls, file_path: str) -> Dict[str, Any]:
        """シート名一覧とセル数のみ軽量取得 (v3.0移植)"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zp:
                # 1. シートIDとシート名のマッピング取得 (workbook.xml)
                sheet_list = []
                with zp.open('xl/workbook.xml') as f:
                    xml_content = cls.encoding_manager.safe_decode(f.read()).text
                    root = ET.fromstring(xml_content.encode('utf-8'))
                    for sheet in root.findall('.//s:sheet', cls.NAMESPACE):
                        s_id = sheet.get('sheetId')
                        s_name = sheet.get('name')
                        r_id = sheet.get(f"{{{cls.NAMESPACE['r']}}}id")
                        if s_id and s_name and r_id:
                            sheet_list.append({
                                'name': s_name,
                                'sheet_id': int(s_id),
                                'r_id': r_id
                            })
                
                # 2. シートIDとファイルパスのマッピング取得 (xl/_rels/workbook.xml.rels)
                rel_to_path = {}
                with zp.open('xl/_rels/workbook.xml.rels') as f:
                    xml_content = cls.encoding_manager.safe_decode(f.read()).text
                    root = ET.fromstring(xml_content.encode('utf-8'))
                    for rel in root.findall('.//rel:Relationship', cls.NAMESPACE):
                        r_id = rel.get('Id')
                        r_target = rel.get('Target')
                        if r_id and r_target:
                            rel_to_path[r_id] = f"xl/{r_target}"
                
                # 3. 各シートのセル数をカウント
                ns_s = cls.NAMESPACE['s']
                tag_c = f"{{{ns_s}}}c"
                
                for sheet_info in sheet_list:
                    xml_path = rel_to_path.get(sheet_info['r_id'])
                    cell_count = 0
                    
                    if xml_path and xml_path in zp.namelist():
                        with zp.open(xml_path) as f:
                            xml_content = cls.encoding_manager.safe_decode(f.read()).text
                            root = ET.fromstring(xml_content.encode('utf-8'))
                            for elem in root.iter(tag_c):
                                # 値を持つセルのみカウント
                                v_elem = elem.find(f'.//{{{ns_s}}}v')
                                is_elem = elem.find(f'.//{{{ns_s}}}is')
                                if v_elem is not None or is_elem is not None:
                                    cell_count += 1
                    
                    sheet_info['cell_count'] = cell_count
                    del sheet_info['r_id']
                
                return {
                    "type": "xlsx",
                    "mode": "sheets",
                    "sheets": sheet_list,
                    "statistics": {
                        "sheet_count": len(sheet_list),
                        "total_cells": sum(s['cell_count'] for s in sheet_list)
                    }
                }
        except Exception as e:
            return {
                "error": f"Failed to get sheet summary: {str(e)}",
                "details": "File may be corrupted or not a valid Excel document"
            }

    @classmethod
    def get_xlsx_content(
        cls, file_path: str, on_error: Optional[Callable[[str, Exception], None]] = None,
        target_sheets: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Excelファイルからシート名・セル番地付きでテキストを抽出します。"""
        results = []
        try:
            with zipfile.ZipFile(file_path, "r") as zp:
                # 1. 共有文字列のロード (richText対応: <si> 単位で結合)
                shared_strings = cls._load_shared_strings(zp)

                # 2. シートIDとシート名のマッピング取得 (workbook.xml)
                sheet_id_to_name = {}
                with zp.open("xl/workbook.xml") as f:
                    xml_content = cls.encoding_manager.safe_decode(f.read()).text
                    root = ET.fromstring(xml_content.encode('utf-8'))
                    for sheet in root.findall(".//s:sheet", cls.NAMESPACE):
                        s_id = sheet.get(f"{{{cls.NAMESPACE['r']}}}id")
                        s_name = sheet.get("name")
                        if s_id and s_name:
                            sheet_id_to_name[s_id] = s_name

                # 3. シートIDとファイルパスのマッピング取得 (xl/_rels/workbook.xml.rels)
                rel_to_path = {}
                with zp.open("xl/_rels/workbook.xml.rels") as f:
                    xml_content = cls.encoding_manager.safe_decode(f.read()).text
                    root = ET.fromstring(xml_content.encode('utf-8'))
                    for rel in root.findall(".//rel:Relationship", cls.NAMESPACE):
                        r_id = rel.get("Id")
                        r_target = rel.get("Target")
                        if r_id and r_target:
                            rel_to_path[r_id] = f"xl/{r_target}"

                # 4. 各ワークシートのパース
                ns_s = cls.NAMESPACE["s"]
                tag_c = f"{{{ns_s}}}c"
                tag_v = f"{{{ns_s}}}v"
                tag_is = f"{{{ns_s}}}is"
                tag_t = f"{{{ns_s}}}t"

                for r_id, sheet_name in sheet_id_to_name.items():
                    # フィルタ指定がある場合は対象外のシートをスキップ
                    if target_sheets is not None and sheet_name not in target_sheets:
                        continue

                    xml_path = rel_to_path.get(r_id)
                    if not xml_path or xml_path not in zp.namelist():
                        continue

                    with zp.open(xml_path) as f:
                        xml_content = cls.encoding_manager.safe_decode(f.read()).text
                        root = ET.fromstring(xml_content.encode('utf-8'))
                        
                        for cell_elem in root.iter(tag_c):
                            current_cell_ref = cell_elem.get("r", "")
                            cell_type = cell_elem.get("t", "")
                            display_text = ""

                            if cell_type == "inlineStr":
                                is_elem = cell_elem.find(tag_is)
                                if is_elem is not None:
                                    parts = []
                                    for t_elem in is_elem.iter(tag_t):
                                        if t_elem.text:
                                            parts.append(t_elem.text)
                                    display_text = "".join(parts)
                            elif cell_type == "s":
                                v_elem = cell_elem.find(tag_v)
                                if v_elem is not None and v_elem.text is not None:
                                    idx = int(v_elem.text)
                                    display_text = shared_strings[idx] if 0 <= idx < len(shared_strings) else ""
                            elif cell_type == "str":
                                v_elem = cell_elem.find(tag_v)
                                if v_elem is not None and v_elem.text is not None:
                                    display_text = v_elem.text
                            else:
                                v_elem = cell_elem.find(tag_v)
                                if v_elem is not None and v_elem.text is not None:
                                    display_text = v_elem.text

                            if display_text:
                                results.append(
                                    {
                                        "text": display_text,
                                        "location": f"{sheet_name}!{current_cell_ref}",
                                        "metadata": {"sheet": sheet_name, "cell": current_cell_ref},
                                    }
                                )

        except Exception as e:
            if on_error:
                on_error(f"Error parsing XLSX {file_path}", e)
        return results

    @classmethod
    def _load_shared_strings(cls, zp: zipfile.ZipFile) -> List[str]:
        """sharedStrings.xml からリッチテキスト対応で共有文字列を読み込む。"""
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" not in zp.namelist():
            return shared_strings

        ns_s = cls.NAMESPACE["s"]
        tag_si = f"{{{ns_s}}}si"
        tag_t = f"{{{ns_s}}}t"

        with zp.open("xl/sharedStrings.xml") as f:
            xml_content = cls.encoding_manager.safe_decode(f.read()).text
            root = ET.fromstring(xml_content.encode('utf-8'))
            for si_elem in root.iter(tag_si):
                parts = []
                for t_elem in si_elem.iter(tag_t):
                    if t_elem.text:
                        parts.append(t_elem.text)
                shared_strings.append("".join(parts))

        return shared_strings

    @classmethod
    def _get_pptx_paragraphs(cls, f: Any, tag_p: str, tag_t: str) -> List[str]:
        """PPTX の XML ファイルから <a:p> パラグラフ単位でテキストを抽出する。"""
        paragraphs: List[str] = []
        current_parts: List[str] = []
        try:
            xml_content = cls.encoding_manager.safe_decode(f.read()).text
            root = ET.fromstring(xml_content.encode('utf-8'))
            for p_elem in root.iter(tag_p):
                for t_elem in p_elem.iter(tag_t):
                    if t_elem.text:
                        current_parts.append(t_elem.text)
                text = "".join(current_parts).strip()
                if text:
                    paragraphs.append(text)
                current_parts = []
        except Exception:
            pass
        return paragraphs

    @classmethod
    def get_pptx_content(
        cls, file_path: str, on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> List[Dict[str, Any]]:
        """PowerPointファイルからスライド番号・ノート付きでテキストを抽出します。"""
        import re

        results: List[Dict[str, Any]] = []
        try:
            with zipfile.ZipFile(file_path, "r") as zp:
                namelist = zp.namelist()

                def get_slide_num(filename: str) -> int:
                    match = re.search(r"(\d+)", filename.split("/")[-1])
                    return int(match.group(1)) if match else 0

                # スライドXMLをスライド番号順にソート
                slide_files = sorted(
                    [n for n in namelist if re.match(r"ppt/slides/slide(\d+)\.xml$", n)],
                    key=get_slide_num,
                )

                ns_a = cls.NAMESPACE["a"]
                tag_p = f"{{{ns_a}}}p"
                tag_t = f"{{{ns_a}}}t"

                for slide_xml in slide_files:
                    m = re.search(r"slide(\d+)\.xml$", slide_xml)
                    slide_num = int(m.group(1)) if m else 0
                    slide_label = f"スライド {slide_num}"

                    # スライド本文のテキスト抽出
                    with zp.open(slide_xml) as f:
                        paragraphs = cls._get_pptx_paragraphs(f, tag_p, tag_t)
                        for i, text in enumerate(paragraphs, 1):
                            results.append(
                                {
                                    "text": text,
                                    "location": f"{slide_label} P.{i}",
                                    "metadata": {"slide": slide_num, "type": "slide"},
                                }
                            )

                    # ノートのテキスト抽出 (存在する場合のみ)
                    notes_xml = f"ppt/notesSlides/notesSlide{slide_num}.xml"
                    if notes_xml in namelist:
                        with zp.open(notes_xml) as f:
                            paragraphs = cls._get_pptx_paragraphs(f, tag_p, tag_t)
                            for i, text in enumerate(paragraphs, 1):
                                results.append(
                                    {
                                        "text": text,
                                        "location": f"{slide_label} (ノート) P.{i}",
                                        "metadata": {"slide": slide_num, "type": "notes"},
                                    }
                                )

        except Exception as e:
            if on_error:
                on_error(f"Error parsing PPTX {file_path}", e)
        return results

    @classmethod
    def extract_content(
        cls, file_path: str, on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> List[Dict[str, Any]]:
        """拡張子に応じてコンテンツを抽出します。"""
        ext = file_path.lower()
        if ext.endswith((".docx", ".docm")):
            return cls.get_docx_content(file_path, on_error)
        elif ext.endswith((".xlsx", ".xlsm")):
            return cls.get_xlsx_content(file_path, on_error)
        elif ext.endswith((".pptx", ".pptm")):
            return cls.get_pptx_content(file_path, on_error)
        return []
