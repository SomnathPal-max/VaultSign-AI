"""
Unit tests for Pushback Email Generator
Tests tone options (Friendly, Neutral, Firm), placeholder formatting, and cash flow justification.
"""

import pytest
from app.pushback import PushbackGenerator

def test_pushback_net_90_example():
    quote = "payment terms are Net-90 days"
    email = PushbackGenerator.generate_email(
        clause_family="extended_payment",
        verbatim_quote=quote,
        clause_reference="Section 2.1",
        tone="friendly",
        user_name="Jordan Reed",
        client_name="Taylor Swift Media",
        project_name="Web Redesign",
        custom_justification="To align with my standard operational cash flow, I kindly request adjusting the payment terms from Net-90 to Net-30."
    )
    
    assert "Jordan Reed" in email.body
    assert "Taylor Swift Media" in email.body
    assert "Web Redesign" in email.subject
    assert "standard operational cash flow" in email.body
    assert "Net-30" in email.body

def test_pushback_tone_options():
    quote = "Contractor assigns all rights perpetually"
    for tone in ["friendly", "neutral", "firm"]:
        email = PushbackGenerator.generate_email(
            clause_family="ip_transfer",
            verbatim_quote=quote,
            tone=tone,
            user_name="Alex",
            client_name="Client Co"
        )
        assert email.tone == tone
        assert "Alex" in email.body
        assert "Client Co" in email.body
        assert len(email.body) > 50
