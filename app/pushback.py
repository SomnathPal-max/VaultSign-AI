"""
VaultSign AI - Context-Aware Pushback Email Generator
Generates polite, professional, and firm correspondence to negotiate flagged contract clauses.
Includes tone options (friendly, neutral, firm), local placeholders, and editable justifications.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel

class PushbackEmail(BaseModel):
    subject: str
    body: str
    tone: str
    clause_family: str
    clause_reference: str
    verbatim_quote: str
    suggested_amendment: str
    ready_to_send: str

EMAIL_TEMPLATES = {
    "extended_payment": {
        "friendly": {
            "subject": "Quick question on payment terms - {project_name}",
            "opening": "Hi {client_name},\n\nThank you so much for sending over the agreement for {project_name}! I'm really excited about partnering together on this project.",
            "core": "I noticed in {clause_reference} that payment terms are currently set to extended terms ({verbatim_quote}). To align with my standard operational cash flow and self-employed overhead, I kindly request adjusting the payment terms to Net-30.",
            "justification": "{custom_justification}",
            "closing": "Please let me know if updating to Net-30 works on your end so we can finalize the contract and kick off our work together!\n\nBest regards,\n{user_name}"
        },
        "neutral": {
            "subject": "Review of {project_name} Agreement - Payment Terms",
            "opening": "Dear {client_name},\n\nI have completed my initial review of the agreement for {project_name}. Everything looks great overall, with one requested revision regarding billing terms.",
            "core": "Regarding {clause_reference} ({verbatim_quote}): As an independent consultant, my practice operates on Net-30 terms upon receipt of invoice. Extended terms create an operational mismatch for solo service delivery.",
            "justification": "{custom_justification}",
            "closing": "Could we please update this clause to Net-30? Once revised, I will be ready to execute the agreement immediately.\n\nSincerely,\n{user_name}"
        },
        "firm": {
            "subject": "Contract Amendment Request: Payment Terms - {project_name}",
            "opening": "Dear {client_name},\n\nThank you for transmitting the contract for {project_name}. Before proceeding to signature, we need to address the payment schedule specified in {clause_reference}.",
            "core": "The clause states: \"{verbatim_quote}\". As a business policy, I cannot accept payment terms exceeding 30 calendar days (Net-30) or terms contingent upon third-party approvals.",
            "justification": "{custom_justification}",
            "closing": "Please issue an updated draft reflecting Net-30 payment terms and standard late payment interest of 1.5% monthly. Thank you for your cooperation.\n\nRegards,\n{user_name}"
        },
        "default_justification": "This ensures consistent working capital and aligns with standard freelance invoicing standards."
    },
    "ip_transfer": {
        "friendly": {
            "subject": "Note regarding IP & background tools - {project_name}",
            "opening": "Hi {client_name},\n\nI'm reviewing our agreement and am thrilled to get started on {project_name}!",
            "core": "Regarding {clause_reference} on IP assignment: I am 100% committed to transferring full ownership of all custom deliverables created for you upon receipt of final payment. However, the current language (\"{verbatim_quote}\") doesn't carve out my pre-existing libraries, starter code, and design tools that I utilize across client projects.",
            "justification": "{custom_justification}",
            "closing": "I'd like to insert a standard clause clarifying that background tools remain my property while you receive a perpetual license to use them as part of the deliverables. Does that sound good to you?\n\nWarmly,\n{user_name}"
        },
        "neutral": {
            "subject": "Requested Revision: Intellectual Property Assignment - {project_name}",
            "opening": "Dear {client_name},\n\nI have reviewed the agreement for {project_name} and would like to propose a standard refinement to {clause_reference}.",
            "core": "The current assignment clause (\"{verbatim_quote}\") conveys all rights immediately and unconditionally, without excluding pre-existing contractor materials or conditioning transfer on full payment.",
            "justification": "{custom_justification}",
            "closing": "I request amending the section so that final assignment takes effect upon full payment of fees, with contractor retaining ownership of background tools subject to a perpetual client license. I have attached sample language below.\n\nBest regards,\n{user_name}"
        },
        "firm": {
            "subject": "Contract Amendment: IP Assignment & Carve-Out - {project_name}",
            "opening": "Dear {client_name},\n\nIn reviewing {clause_reference} of the {project_name} agreement, the intellectual property provision requires immediate amendment.",
            "core": "The current clause (\"{verbatim_quote}\") is overly broad. I retain sole proprietary title to all pre-existing software, frameworks, and tools. Furthermore, no copyright assignment can legally execute prior to full receipt of contractual compensation.",
            "justification": "{custom_justification}",
            "closing": "Please modify {clause_reference} to state that IP in custom deliverables transfers strictly upon receipt of full payment, and that pre-existing contractor assets are explicitly carved out.\n\nSincerely,\n{user_name}"
        },
        "default_justification": "This protects both parties by ensuring you receive clean commercial rights while preserving the pre-existing tools I rely on to deliver professional services."
    },
    "broad_non_compete": {
        "friendly": {
            "subject": "Question regarding non-compete clause - {project_name}",
            "opening": "Hi {client_name},\n\nI'm so looking forward to collaborating on {project_name}!",
            "core": "In reading through {clause_reference}, I spotted a non-compete restriction (\"{verbatim_quote}\"). Because I run an independent freelance business providing specialized services across the industry, I cannot agree to broad restrictions that prevent me from serving other clients.",
            "justification": "{custom_justification}",
            "closing": "I am completely happy to sign strict confidentiality and non-disclosure commitments to protect your proprietary information. Could we please strike the non-compete or replace it with standard confidentiality language?\n\nBest,\n{user_name}"
        },
        "neutral": {
            "subject": "Revision Request: Non-Competition Covenant - {project_name}",
            "opening": "Dear {client_name},\n\nThank you for the agreement for {project_name}. One item in {clause_reference} requires modification before we execute.",
            "core": "The non-compete restriction (\"{verbatim_quote}\") is broader than appropriate for an independent contractor relationship and restricts my ongoing business operations across the industry.",
            "justification": "{custom_justification}",
            "closing": "I propose replacing this section with a robust confidentiality and customer non-solicitation agreement, which will fully protect your business interests without restricting my freelance practice.\n\nRegards,\n{user_name}"
        },
        "firm": {
            "subject": "Required Amendment: Striking Non-Compete Clause - {project_name}",
            "opening": "Dear {client_name},\n\nRegarding the contract for {project_name}, {clause_reference} presents an unacceptable barrier to signature.",
            "core": "The restrictive covenant states: \"{verbatim_quote}\". As an independent contractor, I do not sign general non-competes. In many jurisdictions, such post-engagement restrictions on 1099/contractors are legally unenforceable.",
            "justification": "{custom_justification}",
            "closing": "Please remove {clause_reference} entirely. My standard NDA and confidentiality protections will govern all proprietary and trade secret information.\n\nSincerely,\n{user_name}"
        },
        "default_justification": "Independent contractors must maintain the legal and commercial freedom to offer their specialized skills to non-conflicting clients."
    },
    "asymmetric_liability": {
        "friendly": {
            "subject": "Thought on the indemnification terms - {project_name}",
            "opening": "Hi {client_name},\n\nHope your week is going great! I'm reviewing the {project_name} paperwork.",
            "core": "Looking at {clause_reference} (\"{verbatim_quote}\"), the indemnity is currently uncapped and one-sided. As a boutique provider, my professional liability insurance requires a liability cap tied to our project fee.",
            "justification": "{custom_justification}",
            "closing": "Could we make the indemnification mutual and cap total liability to the total fees paid under this agreement? That keeps everything balanced and protected for both of us!\n\nBest,\n{user_name}"
        },
        "neutral": {
            "subject": "Contract Review: Mutual Indemnification & Liability Cap - {project_name}",
            "opening": "Dear {client_name},\n\nI have reviewed the indemnification provisions in {clause_reference} for {project_name}.",
            "core": "The clause currently holds the contractor to unlimited indemnity (\"{verbatim_quote}\") without reciprocity or standard aggregate liability caps.",
            "justification": "{custom_justification}",
            "closing": "I request amending {clause_reference} to include a mutual liability limitation capped at the total fees paid under the contract, excluding willful misconduct. Please find suggested text below.\n\nRegards,\n{user_name}"
        },
        "firm": {
            "subject": "Required Amendment: Liability Cap & Mutual Indemnity - {project_name}",
            "opening": "Dear {client_name},\n\nI cannot execute the {project_name} contract with {clause_reference} in its current form.",
            "core": "The provision (\"{verbatim_quote}\") imposes uncapped, unilateral liability and consequential damages on the contractor. Commercial risk must be proportionate to the contract value.",
            "justification": "{custom_justification}",
            "closing": "The agreement must incorporate a mutual aggregate liability cap equal to total project fees paid, and expressly exclude incidental and consequential damages. Please provide a revised draft.\n\nSincerely,\n{user_name}"
        },
        "default_justification": "This establishes standard commercial proportionality and complies with business insurance coverage requirements."
    }
}

class PushbackGenerator:
    """Generates context-aware, editable counter-offer emails for any flagged clause."""

    @classmethod
    def generate_email(
        cls,
        clause_family: str,
        verbatim_quote: str,
        clause_reference: str = "the agreement",
        tone: str = "friendly",
        user_name: str = "[Your Name]",
        client_name: str = "[Client Name]",
        project_name: str = "[Project Name]",
        custom_justification: Optional[str] = None
    ) -> PushbackEmail:
        """Constructs personalized email based on family, tone, and user inputs."""
        tone = tone.lower() if tone.lower() in ["friendly", "neutral", "firm"] else "neutral"
        family_data = EMAIL_TEMPLATES.get(clause_family, EMAIL_TEMPLATES["extended_payment"])
        tone_data = family_data.get(tone, family_data["neutral"])

        justification_text = custom_justification or family_data.get("default_justification", "This ensures standard business operational alignment.")

        # Truncate quote for email readability if very long
        quote_display = verbatim_quote.strip()
        if len(quote_display) > 200:
            quote_display = quote_display[:197] + "..."

        format_dict = {
            "client_name": client_name,
            "user_name": user_name,
            "project_name": project_name,
            "clause_reference": clause_reference,
            "verbatim_quote": quote_display,
            "custom_justification": justification_text
        }

        subject = tone_data["subject"].format(**format_dict)
        opening = tone_data["opening"].format(**format_dict)
        core = tone_data["core"].format(**format_dict)
        justification_body = tone_data["justification"].format(**format_dict)
        closing = tone_data["closing"].format(**format_dict)

        full_body = f"{opening}\n\n{core}\n\n{justification_body}\n\n{closing}"
        
        suggested_amendment = (
            f"Suggested Replacement for {clause_reference}:\n"
            f"\"The parties agree that terms under this section shall be amended to standard industry practices, "
            f"limiting obligations to mutual, bilateral commitments and capped liability.\""
        )

        ready_to_send = f"SUBJECT: {subject}\n\n{full_body}"

        return PushbackEmail(
            subject=subject,
            body=full_body,
            tone=tone,
            clause_family=clause_family,
            clause_reference=clause_reference,
            verbatim_quote=verbatim_quote,
            suggested_amendment=suggested_amendment,
            ready_to_send=ready_to_send
        )
