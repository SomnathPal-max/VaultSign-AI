"""
Unit tests for VaultSign AI Verifier Engine
Validates that authentic quotes pass and fabricated/hallucinated quotes are strictly dropped.
"""

import pytest
from app.parser import parse_document
from app.verifier import ContractVerifier, VerificationResult

CONTRACT_SAMPLE = """
MASTER SERVICES AGREEMENT
SECTION 1. PAYMENT
Client shall pay invoices within ninety (90) days of receipt (Net-90).

SECTION 2. INTELLECTUAL PROPERTY
Contractor hereby assigns all right, title and interest in all deliverables perpetually throughout the universe.
"""

@pytest.fixture
def parsed_doc():
    return parse_document(CONTRACT_SAMPLE.encode("utf-8"), "test.txt")

def test_verifier_accepts_verbatim_quote(parsed_doc):
    quote = "Client shall pay invoices within ninety (90) days of receipt (Net-90)."
    res = ContractVerifier.verify_quote(quote, parsed_doc)
    assert res.is_verified is True
    assert res.page_number == 1
    assert res.matched_text == quote
    assert res.drop_reason is None

def test_verifier_accepts_quote_with_normalized_spacing(parsed_doc):
    quote = "Client   shall   pay invoices within ninety (90) days"
    res = ContractVerifier.verify_quote(quote, parsed_doc)
    assert res.is_verified is True
    assert res.page_number == 1

def test_verifier_drops_fabricated_hallucination(parsed_doc):
    # This clause does NOT exist in the sample contract
    fabricated_quote = "Contractor agrees to indemnify client up to ten million dollars for any damages."
    res = ContractVerifier.verify_quote(fabricated_quote, parsed_doc)
    assert res.is_verified is False
    assert "Dropped" in res.drop_reason
    assert res.matched_text is None

def test_verifier_drops_empty_or_too_short(parsed_doc):
    res = ContractVerifier.verify_quote("short", parsed_doc)
    assert res.is_verified is False
    assert "too short" in res.drop_reason
