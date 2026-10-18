"""
VaultSign AI - Multi-Agent Negotiation Simulator (Pro)
Simulates an adversarial debate between The Advocate, The Corporate Counsel, and The Mediator
to stress-test flagged clauses and craft balanced compromise language with strict guardrails.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .parser import ParsedDocument
from .verifier import ContractVerifier
from .ollama_client import OllamaClient
from .analyzer import ClauseFlag

class AgentTurn(BaseModel):
    role: str           # "The Advocate", "The Corporate Counsel", "The Mediator"
    objective: str
    guardrail: str
    statement: str
    cited_quote: Optional[str] = None
    arguments: List[str] = []

class NegotiationDebate(BaseModel):
    clause_family: str
    clause_label: str
    original_quote: str
    turns: List[AgentTurn]
    compromise_clause: str
    actionable_talking_points: List[str]
    guardrail_notice: str
    is_verified: bool

class MultiAgentSimulator:
    """Orchestrates Advocate vs Corporate Counsel vs Mediator debate."""

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama = ollama_client or OllamaClient()

    def simulate_clause_debate(
        self,
        flag: ClauseFlag,
        doc: ParsedDocument,
        model_name: Optional[str] = None
    ) -> NegotiationDebate:
        """
        Runs the 3-agent negotiation simulation for a specific flagged clause.
        Uses Ollama if available; falls back to deterministic expert debate templates.
        """
        original_quote = flag.verbatim_quote or "Unspecified clause text"

        if self.ollama.is_available():
            llm_result = self._simulate_via_ollama(flag, doc, model_name=model_name)
            if llm_result:
                return llm_result

        # Fallback to high-fidelity expert debate simulation
        return self._simulate_deterministic(flag, doc)

    def _simulate_deterministic(
        self,
        flag: ClauseFlag,
        doc: ParsedDocument
    ) -> NegotiationDebate:
        """Generates realistic debate arguments and compromise clauses with v2 guardrails."""
        family = flag.clause_family
        quote = flag.verbatim_quote or ""

        debates_db = {
            "extended_payment": {
                "advocate": (
                    f"The payment term '{quote}' severely harms the freelancer's working capital. "
                    "Waiting 60 to 90 days forces the contractor to act as an interest-free bank for the client. "
                    "Incurred business expenses and taxes cannot wait three months."
                ),
                "advocate_args": [
                    "Cash flow disruption and uncompensated credit risk",
                    "Mismatch between immediate delivery and delayed compensation",
                    "Disproportionate burden on solo operator"
                ],
                "counsel": (
                    "Corporate payment cycles operate on standard monthly billing and vendor reconciliation batches. "
                    "Net-60 or Net-90 allows departmental cross-checks and accounts payable processing. "
                    "(Note: This is corporate argument, not an established legal necessity)."
                ),
                "counsel_args": [
                    "Accounts payable monthly batching cycle",
                    "Departmental sign-off and milestone acceptance protocol",
                    "Enterprise standard vendor onboarding policies"
                ],
                "mediator": (
                    "Compromise proposal: Adjust terms to Net-30 from invoice receipt. "
                    "Alternatively, structure payments into two tranches: a 50% deposit upon milestone sign-off, "
                    "with the remaining 50% on Net-30 terms."
                ),
                "compromise": (
                    "Payment shall be due within thirty (30) days of Client's receipt of undisputed invoice. "
                    "If Client fails to pay within 30 days, interest at 1.5% per month or the statutory maximum shall accrue."
                ),
                "talking_points": [
                    "Explain that your accounting software enforces Net-30 as standard business practice.",
                    "Offer electronic payment options (ACH/card) to streamline their accounts payable process.",
                    "Propose a 2% early-pay discount (2/10 Net 30) as an incentive."
                ]
            },
            "ip_transfer": {
                "advocate": (
                    f"Clause '{quote}' demands an unconstrained perpetual assignment before final payment, "
                    "and contains no carve-out for pre-existing libraries, scripts, or foundational tools. "
                    "This could legally transfer ownership of the freelancer's proprietary starter kits to the client."
                ),
                "advocate_args": [
                    "Assignment before payment deprives contractor of payment leverage",
                    "Lack of background IP carve-out threatens future career work",
                    "Perpetual surrender of pre-existing development assets"
                ],
                "counsel": (
                    "The client is funding the project and requires complete exclusivity over the custom deliverables "
                    "to prevent competitors from using the same assets. "
                    "(Note: This argument reflects client commercial interest, not statutory requirement)."
                ),
                "counsel_args": [
                    "Securing clean chain of title for investors and acquirers",
                    "Preventing leakage of proprietary business logic",
                    "Ensuring full commercial exclusivity"
                ],
                "mediator": (
                    "Compromise proposal: Transfer copyright to final deliverables ONLY upon full and final payment, "
                    "while retaining contractor ownership of pre-existing tools, templates, and general know-how, "
                    "granting client a perpetual, non-exclusive license to use them."
                ),
                "compromise": (
                    "Condition of Assignment: Intellectual property rights in Final Deliverables shall transfer to Client "
                    "solely upon full and complete payment of all agreed fees. Contractor retains sole ownership of "
                    "all Pre-Existing Materials and general tools, and hereby grants Client a non-exclusive, perpetual, "
                    "worldwide license to use such Pre-Existing Materials solely as incorporated in the Deliverables."
                ),
                "talking_points": [
                    "Clarify that background tools allow you to deliver faster and at lower cost to the client.",
                    "Confirm the client receives full ownership of the final work product once paid.",
                    "Highlight that withholding title until payment is standard commercial practice."
                ]
            },
            "broad_non_compete": {
                "advocate": (
                    f"The non-compete clause '{quote}' attempts to freeze the freelancer out of their core market. "
                    "A broad non-compete without geographic limits or narrow competitor definitions effectively "
                    "denies the freelancer their right to earn a livelihood."
                ),
                "advocate_args": [
                    "Direct restraint on future trade and freelance livelihood",
                    "Overly broad temporal and geographic scope",
                    "Independent contractors cannot be treated as tied employees"
                ],
                "counsel": (
                    "The client must protect its confidential trade secrets, client rosters, and strategic product plans "
                    "from being transferred to direct competitors in the same vertical. "
                    "(Note: Non-competes against independent contractors face high judicial scrutiny)."
                ),
                "counsel_args": [
                    "Preventing immediate reuse of confidential insights",
                    "Protecting client customer relationships",
                    "Mitigating competitive poaching"
                ],
                "mediator": (
                    "Compromise proposal: Strike the non-compete clause in its entirety and replace it with a rigorous, "
                    "watertight Non-Disclosure and Confidentiality clause, plus a targeted non-solicitation of active client accounts."
                ),
                "compromise": (
                    "In lieu of non-competition, Contractor agrees to maintain the strict confidentiality of Client's "
                    "Confidential Information and agrees not to directly solicit Client's active existing customers "
                    "for a period of six (6) months following termination of this Agreement."
                ),
                "talking_points": [
                    "Point out that confidentiality agreements fully protect their trade secrets without banning your career.",
                    "Mention that non-competes on contractors are unenforceable in many jurisdictions (e.g. California).",
                    "Offer an explicit list of named direct competitors if absolute exclusion is required."
                ]
            },
            "asymmetric_liability": {
                "advocate": (
                    f"The clause '{quote}' places unlimited, one-sided liability on the contractor. "
                    "A $5,000 project should never expose a freelancer to multimillion-dollar consequential claims or legal fees."
                ),
                "advocate_args": [
                    "Uncapped indemnity creates existential personal financial risk",
                    "Asymmetric terms: client offers zero reciprocal indemnity",
                    "Consequential and punitive damages are not excluded"
                ],
                "counsel": (
                    "Client standard vendor policies mandate full defense against third-party intellectual property or negligence claims. "
                    "(Note: Enterprise boilerplate often defaults to uncapped indemnity unless negotiated)."
                ),
                "counsel_args": [
                    "Protection against third-party copyright or patent infringement",
                    "Corporate risk minimization compliance standards",
                    "Ensuring vendor accountability"
                ],
                "mediator": (
                    "Compromise proposal: Make indemnification mutual and reciprocal, restrict indemnity to willful misconduct "
                    "or gross negligence, and strictly cap total liability at the total fees paid under the contract."
                ),
                "compromise": (
                    "Mutual Limitation of Liability: Except for breaches of confidentiality or gross negligence, "
                    "each party's maximum aggregate liability arising under this Agreement shall be capped at the total amount "
                    "of fees paid or payable by Client to Contractor under this Agreement in the twelve (12) months preceding the claim. "
                    "Neither party shall be liable for indirect, incidental, or consequential damages."
                ),
                "talking_points": [
                    "Explain that freelancer insurance policies require liability caps tied to project fee totals.",
                    "Emphasize that mutual liability establishes a fair partnership.",
                    "Point out that no commercial insurer covers open-ended consequential liabilities."
                ]
            }
        }

        # Generic template for other 4 families
        data = debates_db.get(family, {
            "advocate": f"The clause '{quote}' creates significant operational risk by placing uncompensated burdens on the freelancer.",
            "advocate_args": ["Unilateral risk shift", "Uncertain scope of obligations", "Lack of reciprocal client commitments"],
            "counsel": "The client seeks operational predictability and quality assurance under standard master service agreements.",
            "counsel_args": ["Standard enterprise terms", "Quality assurance benchmark", "Project risk mitigation"],
            "mediator": "Compromise proposal: Clarify milestones, establish mutual notice, and set clear caps on revisions or cancellation terms.",
            "compromise": f"The parties agree that obligations under this section shall be reasonable, bilateral, and subject to written mutual agreement.",
            "talking_points": [
                "Request written mutual approval rather than unilateral client discretion.",
                "Frame changes around keeping the delivery timeline on schedule.",
                "Suggest standard industry benchmark parameters."
            ]
        })

        turns = [
            AgentTurn(
                role="The Advocate",
                objective="Identify any clause that limits the freelancer's future earning potential or delays compensation.",
                guardrail="Must quote the clause it criticizes.",
                statement=data["advocate"],
                cited_quote=quote,
                arguments=data["advocate_args"]
            ),
            AgentTurn(
                role="The Corporate Counsel",
                objective="Defend the contract as written; justify clauses as standard practice.",
                guardrail="Must not invent legal precedent; claims of 'standard practice' are arguments, not facts.",
                statement=data["counsel"],
                arguments=data["counsel_args"]
            ),
            AgentTurn(
                role="The Mediator",
                objective="Synthesize the debate and generate a compromise clause.",
                guardrail="Compromise wording is a suggested talking point to review with a qualified lawyer.",
                statement=data["mediator"],
                arguments=["Balanced mutual risk sharing", "Clear written timelines"]
            )
        ]

        return NegotiationDebate(
            clause_family=family,
            clause_label=flag.family_label,
            original_quote=quote,
            turns=turns,
            compromise_clause=data["compromise"],
            actionable_talking_points=data["talking_points"],
            guardrail_notice="NOTICE: Compromise clauses are drafting suggestions for negotiation discussion, not binding legal counsel.",
            is_verified=flag.is_verified
        )

    def _simulate_via_ollama(
        self,
        flag: ClauseFlag,
        doc: ParsedDocument,
        model_name: Optional[str] = None
    ) -> Optional[NegotiationDebate]:
        """Runs the 3-role simulation using local Ollama model."""
        prompt = (
            f"Simulate a 3-agent negotiation review on this contract clause:\n"
            f"CLAUSE TYPE: {flag.family_label}\n"
            f"QUOTED TEXT: \"{flag.verbatim_quote}\"\n\n"
            f"ROLES & STRICT GUARDRAILS:\n"
            f"1. The Advocate: Criticize this clause from the freelancer's view. MUST quote the clause directly.\n"
            f"2. The Corporate Counsel: Defend the contract as written. Justify as corporate practice. Do NOT invent fake legal precedent.\n"
            f"3. The Mediator: Synthesize both views and propose a fair, balanced compromise clause.\n\n"
            f"Respond ONLY in valid JSON format:\n"
            f"{{\n"
            f"  \"advocate_statement\": \"...\",\n"
            f"  \"advocate_arguments\": [\"...\", \"...\"],\n"
            f"  \"counsel_statement\": \"...\",\n"
            f"  \"counsel_arguments\": [\"...\", \"...\"],\n"
            f"  \"mediator_statement\": \"...\",\n"
            f"  \"compromise_clause\": \"<exact replacement contract clause text>\",\n"
            f"  \"talking_points\": [\"...\", \"...\"]\n"
            f"}}"
        )
        
        messages = [
            {"role": "system", "content": "You are VaultSign AI's multi-agent negotiation simulator. Output valid JSON only."},
            {"role": "user", "content": prompt}
        ]

        resp = self.ollama.generate_chat(messages, model=model_name, temperature=0.2)
        if not resp:
            return None

        try:
            cleaned = resp.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            d = json.loads(cleaned)

            turns = [
                AgentTurn(
                    role="The Advocate",
                    objective="Identify any clause that limits the freelancer's future earning potential or delays compensation.",
                    guardrail="Must quote the clause it criticizes.",
                    statement=d.get("advocate_statement", ""),
                    cited_quote=flag.verbatim_quote,
                    arguments=d.get("advocate_arguments", [])
                ),
                AgentTurn(
                    role="The Corporate Counsel",
                    objective="Defend the contract as written; justify clauses as standard practice.",
                    guardrail="Must not invent legal precedent; claims of 'standard practice' are arguments, not facts.",
                    statement=d.get("counsel_statement", ""),
                    arguments=d.get("counsel_arguments", [])
                ),
                AgentTurn(
                    role="The Mediator",
                    objective="Synthesize the debate and generate a compromise clause.",
                    guardrail="Compromise wording is a suggested talking point to review with a qualified lawyer.",
                    statement=d.get("mediator_statement", ""),
                    arguments=["Balanced risk compromise"]
                )
            ]

            return NegotiationDebate(
                clause_family=flag.clause_family,
                clause_label=flag.family_label,
                original_quote=flag.verbatim_quote or "",
                turns=turns,
                compromise_clause=d.get("compromise_clause", ""),
                actionable_talking_points=d.get("talking_points", []),
                guardrail_notice="NOTICE: Compromise clauses are drafting suggestions for negotiation discussion, not binding legal counsel.",
                is_verified=flag.is_verified
            )
        except Exception:
            return None
