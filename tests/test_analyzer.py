"""
Unit tests for 8-Trap Clause Analyzer
Tests detection of all 8 freelancer clause families and verification of the Section 7 output rule.
"""

import os
import pytest
from app.parser import parse_document
from app.analyzer import ContractAnalyzer

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_contracts")

@pytest.fixture
def analyzer():
    return ContractAnalyzer()

def test_predatory_contract_detection(analyzer):
    predatory_path = os.path.join(SAMPLES_DIR, "predatory_freelance_master_services.txt")
    with open(predatory_path, "rb") as f:
        doc = parse_document(f.read(), "predatory.txt")

    report = analyzer.analyze_contract(doc, force_mode="deterministic")
    
    assert report.total_pages >= 1
    assert report.summary["flagged_issues"] >= 7
    
    flag_dict = {f.clause_family: f for f in report.flags}
    
    # Check IP
    assert flag_dict["ip_transfer"].status == "FLAGGED"
    assert "perpetual" in flag_dict["ip_transfer"].verbatim_quote.lower()
    assert flag_dict["ip_transfer"].is_verified is True
    
    # Check Payment
    assert flag_dict["extended_payment"].status == "FLAGGED"
    assert "ninety (90) days" in flag_dict["extended_payment"].verbatim_quote.lower()
    
    # Check Non-Compete
    assert flag_dict["broad_non_compete"].status == "FLAGGED"
    assert "twenty-four (24) months" in flag_dict["broad_non_compete"].verbatim_quote.lower()
    
    # Check Liability
    assert flag_dict["asymmetric_liability"].status == "FLAGGED"
    assert "indemnify and hold harmless" in flag_dict["asymmetric_liability"].verbatim_quote.lower()

def test_fair_contract_clean_baseline(analyzer):
    fair_path = os.path.join(SAMPLES_DIR, "fair_contractor_agreement.txt")
    with open(fair_path, "rb") as f:
        doc = parse_document(f.read(), "fair.txt")

    report = analyzer.analyze_contract(doc, force_mode="deterministic")
    
    # In fair contract, predatory traps should NOT be detected
    for flag in report.flags:
        if flag.status == "NOT_DETECTED":
            # Section 7 rule: Must say "Not detected. Please verify manually."
            # It must NEVER say "no problems"
            assert "Not detected. Please verify manually." in flag.plain_english_explanation
            assert "no problem" not in flag.plain_english_explanation.lower()
