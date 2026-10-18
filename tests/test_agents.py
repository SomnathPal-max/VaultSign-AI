"""
Unit tests for Multi-Agent Negotiation Simulator
Tests Advocate, Corporate Counsel, and Mediator roles and v2 guardrails.
"""

import pytest
from app.parser import parse_document
from app.analyzer import ClauseFlag
from app.agents import MultiAgentSimulator

def test_multi_agent_simulation_roles():
    sim = MultiAgentSimulator()
    sample_text = "Client shall pay invoices within ninety (90) days of receipt (Net-90)."
    doc = parse_document(sample_text.encode("utf-8"), "contract.txt")
    
    flag = ClauseFlag(
        clause_id="f1",
        clause_family="extended_payment",
        family_label="Extended Payment Terms",
        status="FLAGGED",
        risk_level="HIGH",
        verbatim_quote="Client shall pay invoices within ninety (90) days of receipt (Net-90).",
        page_number=1,
        plain_english_explanation="Net-90 forces contractor to float client expenses.",
        suggested_ask="Request Net-30 payment terms.",
        is_verified=True
    )
    
    debate = sim.simulate_clause_debate(flag, doc)
    
    assert len(debate.turns) == 3
    roles = [t.role for t in debate.turns]
    assert "The Advocate" in roles
    assert "The Corporate Counsel" in roles
    assert "The Mediator" in roles
    
    advocate = next(t for t in debate.turns if t.role == "The Advocate")
    assert flag.verbatim_quote in advocate.statement or flag.verbatim_quote in advocate.cited_quote
    
    counsel = next(t for t in debate.turns if t.role == "The Corporate Counsel")
    assert "argument" in counsel.guardrail.lower() or "argument" in counsel.statement.lower()
    
    mediator = next(t for t in debate.turns if t.role == "The Mediator")
    assert len(debate.compromise_clause) > 20
    assert "Compromise" in debate.guardrail_notice or "NOTICE" in debate.guardrail_notice
