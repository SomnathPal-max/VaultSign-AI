"""
Direct synchronous endpoint tests for VaultSign AI Server
Tests all server logic, sample ingestion, debate simulation, pushback generation, and export.
"""

import pytest
from app.server import (
    get_system_status,
    analyze_uploaded_document,
    run_multi_agent_debate,
    generate_pushback_email,
    export_report,
    reset_workspace,
    list_sample_contracts,
    DebateRequest,
    PushbackRequest,
    ExportRequest
)

def test_status_endpoint():
    res = get_system_status()
    assert res["trust_boundary"] == "127.0.0.1 (Strict Localhost)"
    assert res["network_guard"] == "OFFLINE_VERIFIED"
    assert "legal_notice" in res

def test_list_samples_endpoint():
    res = list_sample_contracts()
    assert "samples" in res
    assert len(res["samples"]) >= 3

def test_analyze_sample_endpoint():
    res = analyze_uploaded_document(
        file=None,
        sample_name="predatory_freelance_master_services.txt",
        execution_mode="deterministic"
    )
    assert res["success"] is True
    report = res["report"]
    assert report["filename"] == "predatory_freelance_master_services.txt"
    assert report["summary"]["flagged_issues"] >= 7
    assert len(report["flags"]) == 8

def test_simulate_debate_endpoint():
    # First analyze
    analyze_uploaded_document(
        file=None,
        sample_name="predatory_freelance_master_services.txt",
        execution_mode="deterministic"
    )
    
    # Run debate
    req = DebateRequest(clause_family="extended_payment")
    res = run_multi_agent_debate(req)
    assert res["success"] is True
    debate = res["debate"]
    assert len(debate["turns"]) == 3
    assert len(debate["compromise_clause"]) > 20

def test_generate_pushback_endpoint():
    req = PushbackRequest(
        clause_family="extended_payment",
        tone="friendly",
        user_name="Morgan Davis",
        client_name="Initech Corp",
        project_name="Core Banking Redesign"
    )
    res = generate_pushback_email(req)
    assert res["success"] is True
    email = res["email"]
    assert "Morgan Davis" in email["body"]
    assert "Initech Corp" in email["body"]
    assert "Core Banking Redesign" in email["subject"]

def test_export_markdown_endpoint():
    analyze_uploaded_document(
        file=None,
        sample_name="predatory_freelance_master_services.txt",
        execution_mode="deterministic"
    )
    
    req = ExportRequest(format="markdown")
    res = export_report(req)
    assert "# VaultSign AI" in res.body.decode("utf-8")
    assert "NOT LEGAL ADVICE" in res.body.decode("utf-8")

def test_reset_workspace_endpoint():
    res = reset_workspace()
    assert res["success"] is True
    status = get_system_status()
    assert status["has_loaded_document"] is False
