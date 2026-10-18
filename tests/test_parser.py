"""
Unit tests for VaultSign AI Document Parser
Tests PDF, DOCX, and TXT parsing with page number preservation.
"""

import pytest
import io
import zipfile
import xml.etree.ElementTree as ET
from app.parser import parse_document, normalize_text, ParsedDocument

def test_normalize_text():
    raw = "Here’s a “sample” text with   spaces and—em dashes."
    cleaned = normalize_text(raw)
    assert "'" in cleaned
    assert '"' in cleaned
    assert "-" in cleaned
    assert "  " not in cleaned

def test_parse_txt():
    sample_text = "Page 1 Content\nSection 1. Term\n\x0cPage 2 Content\nSection 2. Payment"
    doc = parse_document(sample_text.encode("utf-8"), "contract.txt")
    assert doc.total_pages == 2
    assert "Page 1 Content" in doc.pages[0].text
    assert "Page 2 Content" in doc.pages[1].text
    assert doc.file_type == "txt"

def test_parse_docx_memory():
    # Build a minimal valid DOCX in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p><w:r><w:t>SECTION 1. PAYMENT TERMS</w:t></w:r></w:p>
                <w:p><w:r><w:t>Payment is Net-90 days.</w:t></w:r></w:p>
                <w:p><w:r><w:br w:type="page"/></w:r></w:p>
                <w:p><w:r><w:t>SECTION 2. TERMINATION</w:t></w:r></w:p>
                <w:p><w:r><w:t>Client may terminate at will without kill fee.</w:t></w:r></w:p>
            </w:body>
        </w:document>
        """
        zf.writestr("word/document.xml", doc_xml)
    
    buf.seek(0)
    doc = parse_document(buf.read(), "agreement.docx")
    assert doc.file_type == "docx"
    assert doc.total_pages >= 2
    assert "Net-90" in doc.full_text
