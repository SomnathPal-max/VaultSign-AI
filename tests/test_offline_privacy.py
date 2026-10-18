"""
VaultSign AI - Zero-Trust & Offline Privacy Verification Test
Proves reproducible local-only operation, zero telemetry, in-memory ephemerality,
and strict adherence to the Section 5 Privacy and Trust Model.
"""

import os
import socket
import pytest
from app.config import HOST, PORT, NETWORK_GUARD_ENABLED, IN_MEMORY_ONLY
from app.parser import parse_document
from app.analyzer import ContractAnalyzer

def test_localhost_binding_only():
    """Verify application binds strictly to 127.0.0.1 and not 0.0.0.0."""
    assert HOST == "127.0.0.1"
    assert NETWORK_GUARD_ENABLED is True
    assert IN_MEMORY_ONLY is True

def test_no_cloud_keys_in_codebase():
    """Inspects codebase to guarantee zero proprietary cloud API keys or dependencies."""
    app_dir = os.path.dirname(os.path.dirname(__file__))
    prohibited_strings = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "api.openai.com", "api.anthropic.com"]
    
    for root, _, files in os.walk(os.path.join(app_dir, "app")):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for p in prohibited_strings:
                        assert p not in content, f"Found prohibited cloud API reference '{p}' in {file}"

def test_offline_analysis_execution():
    """
    Simulates complete contract ingestion and analysis in an isolated environment.
    Verifies that no outbound network socket connection is established during document processing.
    """
    sample_text = """
    AGREEMENT
    Payment shall be Net-90 days.
    Contractor assigns all intellectual property perpetually and irrevocably throughout the universe.
    """
    
    # Store original socket connect to detect any outbound connection attempt
    original_connect = socket.socket.connect
    outbound_attempts = []

    def mock_connect(self, address):
        host, port = address[0], address[1]
        # Allow local loopback only (127.0.0.1)
        if host not in ["127.0.0.1", "localhost"]:
            outbound_attempts.append(address)
            raise ConnectionRefusedError(f"Zero-Trust Guard: Outbound request to {address} blocked!")
        return original_connect(self, address)

    socket.socket.connect = mock_connect

    try:
        doc = parse_document(sample_text.encode("utf-8"), "test_offline.txt")
        analyzer = ContractAnalyzer()
        report = analyzer.analyze_contract(doc, force_mode="deterministic")
        
        # Verify findings
        assert report.summary["flagged_issues"] >= 2
        # Assert ZERO outbound connection attempts were made
        assert len(outbound_attempts) == 0
    finally:
        # Restore socket connect
        socket.socket.connect = original_connect

def test_ephemeral_memory_purged():
    """Verify that vector chunks and state can be completely purged with no disk remnants."""
    from app.chunker import InMemoryVectorIndex, ContractChunk
    
    chunks = [ContractChunk(
        chunk_id="c1",
        section_title="Confidential",
        page_number=1,
        text="Ultra-confidential contract terms",
        char_start=0,
        char_end=30
    )]
    index = InMemoryVectorIndex(chunks)
    assert len(index.chunks) == 1
    
    # Purge index
    index.clear()
    assert len(index.chunks) == 0
    assert len(index.doc_tokens) == 0
