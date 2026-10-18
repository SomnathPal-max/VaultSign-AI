"""
VaultSign AI - Multi-format Document Ingestion & Section Parser
Extracts text from PDF, DOCX, and TXT with strict page and section preservation.
"""

import io
import re
import os
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ParsedPage(BaseModel):
    page_number: int
    text: str
    char_start: int
    char_end: int

class ParsedDocument(BaseModel):
    filename: str
    file_type: str
    total_pages: int
    full_text: str
    pages: List[ParsedPage]
    raw_metadata: Dict[str, Any] = {}

def normalize_text(text: str) -> str:
    """Normalize unicode quotes, dashes, ligatures, and excessive spaces."""
    if not text:
        return ""
    # Ligatures
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff")
    # Quotes & apostrophes
    text = re.sub(r'[\u2018\u2019\u201A\u201B\u2032]', "'", text)
    text = re.sub(r'[\u201C\u201D\u201E\u201F\u2033]', '"', text)
    # Dashes
    text = re.sub(r'[\u2013\u2014\u2015]', "-", text)
    # Non-breaking space & control chars
    text = text.replace("\u00a0", " ")
    # Replace multiple spaces with single space within lines, keep newlines
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]
    return "\n".join(lines).strip()

def parse_pdf(file_bytes: bytes, filename: str = "document.pdf") -> ParsedDocument:
    """Parse PDF using PyMuPDF (fitz) with exact page-by-page text extraction."""
    import pymupdf  # fits requirements
    
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    pages: List[ParsedPage] = []
    full_text_chunks: List[str] = []
    curr_char = 0

    for idx, page in enumerate(doc):
        raw_text = page.get_text("text") or ""
        clean_text = normalize_text(raw_text)
        
        char_len = len(clean_text)
        page_obj = ParsedPage(
            page_number=idx + 1,
            text=clean_text,
            char_start=curr_char,
            char_end=curr_char + char_len
        )
        pages.append(page_obj)
        full_text_chunks.append(clean_text)
        curr_char += char_len + 2  # account for "\n\n" between pages

    doc.close()
    full_text = "\n\n".join(full_text_chunks)
    
    return ParsedDocument(
        filename=filename,
        file_type="pdf",
        total_pages=len(pages),
        full_text=full_text,
        pages=pages,
        raw_metadata={"page_count": len(pages)}
    )

def parse_docx(file_bytes: bytes, filename: str = "document.docx") -> ParsedDocument:
    """
    Parse DOCX using native Python standard library (zipfile + xml.etree).
    Zero external dependencies required. Extracts paragraphs and tables.
    """
    namespaces = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    }
    
    pages: List[ParsedPage] = []
    current_page_text: List[str] = []
    page_num = 1
    curr_char = 0

    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
        if 'word/document.xml' not in zf.namelist():
            raise ValueError("Invalid DOCX format: word/document.xml not found")
        
        doc_xml = zf.read('word/document.xml')
        root = ET.fromstring(doc_xml)

        body = root.find('w:body', namespaces)
        if body is None:
            raise ValueError("Invalid DOCX structure: w:body missing")

        for elem in body:
            # Check for paragraph or table
            tag = elem.tag.split('}')[-1]
            if tag == 'p':
                # Check for explicit page break in runs
                has_page_break = False
                for r in elem.findall('.//w:r', namespaces):
                    if r.find('.//w:br[@w:type="page"]', namespaces) is not None:
                        has_page_break = True

                text_runs = elem.findall('.//w:t', namespaces)
                p_text = "".join([t.text for t in text_runs if t.text])
                p_text_clean = normalize_text(p_text)
                if p_text_clean:
                    current_page_text.append(p_text_clean)

                if has_page_break:
                    page_content = "\n\n".join(current_page_text)
                    page_len = len(page_content)
                    pages.append(ParsedPage(
                        page_number=page_num,
                        text=page_content,
                        char_start=curr_char,
                        char_end=curr_char + page_len
                    ))
                    curr_char += page_len + 2
                    page_num += 1
                    current_page_text = []

            elif tag == 'tbl':
                # Extract table text rows
                table_lines = []
                for row in elem.findall('.//w:tr', namespaces):
                    cell_texts = []
                    for cell in row.findall('.//w:tc', namespaces):
                        c_t = "".join([t.text for t in cell.findall('.//w:t', namespaces) if t.text])
                        cell_texts.append(normalize_text(c_t))
                    if cell_texts:
                        table_lines.append(" | ".join(cell_texts))
                if table_lines:
                    current_page_text.append("\n".join(table_lines))

    # Append remaining page
    page_content = "\n\n".join(current_page_text) if current_page_text else "Empty Document"
    page_len = len(page_content)
    pages.append(ParsedPage(
        page_number=page_num,
        text=page_content,
        char_start=curr_char,
        char_end=curr_char + page_len
    ))

    full_text = "\n\n".join([p.text for p in pages])
    return ParsedDocument(
        filename=filename,
        file_type="docx",
        total_pages=len(pages),
        full_text=full_text,
        pages=pages
    )

def parse_txt(file_bytes: bytes, filename: str = "document.txt") -> ParsedDocument:
    """Parse TXT or Markdown file, handling encoding and page-break characters (\x0c)."""
    try:
        raw_text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raw_text = file_bytes.decode("latin-1", errors="ignore")

    raw_pages = raw_text.split("\x0c") if "\x0c" in raw_text else [raw_text]
    pages: List[ParsedPage] = []
    curr_char = 0
    full_text_chunks: List[str] = []

    for idx, page_raw in enumerate(raw_pages):
        clean_text = normalize_text(page_raw)
        if not clean_text:
            continue
        p_len = len(clean_text)
        pages.append(ParsedPage(
            page_number=idx + 1,
            text=clean_text,
            char_start=curr_char,
            char_end=curr_char + p_len
        ))
        full_text_chunks.append(clean_text)
        curr_char += p_len + 2

    if not pages:
        pages.append(ParsedPage(page_number=1, text="", char_start=0, char_end=0))

    full_text = "\n\n".join(full_text_chunks)
    return ParsedDocument(
        filename=filename,
        file_type="txt",
        total_pages=len(pages),
        full_text=full_text,
        pages=pages
    )

def parse_document(file_bytes: bytes, filename: str) -> ParsedDocument:
    """Router to parse document based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return parse_pdf(file_bytes, filename)
    elif ext in [".docx", ".doc"]:
        return parse_docx(file_bytes, filename)
    elif ext in [".txt", ".md", ".rtf"]:
        return parse_txt(file_bytes, filename)
    else:
        # Default fallback to text parser
        return parse_txt(file_bytes, filename)
