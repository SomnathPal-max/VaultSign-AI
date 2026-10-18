"""
VaultSign AI - 8-Trap Clause Detection & Analysis Engine
Implements the 8 Freelancer Clause Families with Ollama LLM integration,
deterministic baseline pattern matching, and strict Verifier quote confirmation.
"""

import re
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .parser import ParsedDocument
from .chunker import ContractChunk, InMemoryVectorIndex
from .verifier import ContractVerifier, VerificationResult
from .ollama_client import OllamaClient

class ClauseFlag(BaseModel):
    clause_id: str
    clause_family: str
    family_label: str
    status: str  # "FLAGGED" or "NOT_DETECTED"
    risk_level: str  # "HIGH", "MEDIUM", "LOW", "UNVERIFIED"
    verbatim_quote: Optional[str] = None
    page_number: Optional[int] = None
    section_name: Optional[str] = None
    plain_english_explanation: str
    suggested_ask: str
    is_verified: bool = False
    context_snippet: Optional[str] = None
    origin: str = "v1"

class AnalysisReport(BaseModel):
    filename: str
    total_pages: int
    flags: List[ClauseFlag]
    dropped_hallucinations_count: int
    unverified_flags_dropped: List[Dict[str, Any]]
    model_used: str
    execution_mode: str  # "ollama_llm", "deterministic_baseline", "hybrid"
    summary: Dict[str, Any]

CLAUSE_DEFINITIONS = {
    "ip_transfer": {
        "label": "IP Transfer / Work for Hire",
        "origin": "v1",
        "description": "Perpetual or irrevocable assignment; assignment before payment; no carve-out for pre-existing tools or background IP.",
        "default_risk": "HIGH",
        "default_ask": "Carve out pre-existing tools/templates and condition IP transfer upon full and final payment.",
        "search_keywords": ["intellectual property", "work made for hire", "irrevocable", "perpetual", "assignment", "inventions", "all rights"]
    },
    "extended_payment": {
        "label": "Extended Payment Terms",
        "origin": "v1",
        "description": "Net-60, Net-90, or Net-120 payment terms; payment conditional on client acceptance or pay-when-paid clauses.",
        "default_risk": "HIGH",
        "default_ask": "Request Net-15 or Net-30 payment terms with 50% upfront deposit to safeguard cash flow.",
        "search_keywords": ["net 60", "net 90", "net 120", "within 60 days", "within 90 days", "pay when paid", "conditional upon client receiving payment"]
    },
    "broad_non_compete": {
        "label": "Broad Non-Compete",
        "origin": "v1",
        "description": "Excessive duration, global or unlimited geography, restricts offering freelance services to other clients in industry.",
        "default_risk": "HIGH",
        "default_ask": "Narrow non-compete strictly to direct competitors using proprietary trade secrets, or strike non-compete entirely.",
        "search_keywords": ["non-compete", "not engage in any business", "competing business", "restraint of trade", "12 months", "24 months", "worldwide"]
    },
    "asymmetric_liability": {
        "label": "Asymmetric Liability / Indemnification",
        "origin": "v1",
        "description": "One-sided indemnification; uncapped damages; freelancer holds client harmless while client accepts no reciprocal liability.",
        "default_risk": "HIGH",
        "default_ask": "Cap total liability to the total fees paid under the contract and make indemnification mutual and reciprocal.",
        "search_keywords": ["indemnify and hold harmless", "indemnification", "defend and hold", "uncapped liability", "consequential damages", "sole liability"]
    },
    "unlimited_revisions": {
        "label": "Unlimited Revisions / Scope Creep",
        "origin": "v2 (New)",
        "description": "'Until satisfied' or 'to sole satisfaction' language; vague deliverables; lack of formal change-order procedure.",
        "default_risk": "MEDIUM",
        "default_ask": "Specify a maximum of two revision rounds and establish an hourly rate / change order process for extra revisions.",
        "search_keywords": ["sole satisfaction", "until client is satisfied", "unlimited revisions", "reasonable satisfaction", "additional changes without fee"]
    },
    "termination_kill_fee": {
        "label": "Termination & Kill Fee",
        "origin": "v2 (New)",
        "description": "Termination at will by client with no payment for completed work; absence of notice period or kill fee.",
        "default_risk": "HIGH",
        "default_ask": "Require 14-30 days written notice and guarantee pro-rata compensation plus a 25% kill fee for early cancellation.",
        "search_keywords": ["terminate immediately", "terminate for convenience", "without cause", "no further payment", "without compensation for work in progress", "no kill fee"]
    },
    "late_payment_consequences": {
        "label": "Late-Payment Consequences",
        "origin": "v2 (New)",
        "description": "No late fees or statutory interest on overdue invoices; client right to withhold entire payment for disputed items.",
        "default_risk": "MEDIUM",
        "default_ask": "Add 1.5% monthly late interest on overdue balances and restrict payment withholding only to amounts under good-faith dispute.",
        "search_keywords": ["no interest shall accrue", "withhold payment", "disputed amount", "no late penalty", "without interest"]
    },
    "exclusivity": {
        "label": "Exclusivity Restrictions",
        "origin": "v2 (New)",
        "description": "Restrictions preventing contractor from taking on other non-conflicting clients during or following the agreement term.",
        "default_risk": "HIGH",
        "default_ask": "Explicitly confirm contractor's independent contractor status and freedom to provide services to other non-competing clients.",
        "search_keywords": ["exclusive services", "sole and exclusive", "shall not provide services to any other", "devote full time", "exclusive basis"]
    }
}

# Heuristic Patterns for Deterministic Baseline & Pre-filtering
PATTERNS = {
    "ip_transfer": [
        r'(?i)(?:assigns?|transfers?|hereby\s+assigns?)\s+(?:all\s+)?(?:right,\s+title\s+and\s+interest|intellectual\s+property|inventions|works?)(?:[^\.\n;]{0,180})(?:perpetual|irrevocable|worldwide|throughout\s+the\s+universe)',
        r'(?i)(?:work\s+made\s+for\s+hire|work\s+for\s+hire)(?:[^\.\n;]{0,160})(?:sole\s+and\s+exclusive\s+property|client(?:\'s)?\s+property)',
        r'(?i)(?:prior\s+to|regardless\s+of|irrespective\s+of)\s+(?:payment|full\s+payment|receipt\s+of\s+funds)'
    ],
    "extended_payment": [
        r'(?i)(?:within|payable\s+within|payment\s+terms?)\s+(?:sixty|ninety|one\s+hundred\s+twenty|[69]0|120)\s*(?:\([0-9]+\)\s*)?days',
        r'(?i)net[\s\-](?:60|90|120)',
        r'(?i)(?:contingent\s+upon|conditional\s+upon|subject\s+to)\s+(?:client\s+receiving\s+payment|third[\s\-]party\s+payment|approval\s+by\s+client)',
        r'(?i)pay[\s\-]when[\s\-]paid'
    ],
    "broad_non_compete": [
        r'(?i)(?<!no\s)(?<!waive\s)(?<!without\s)(?:shall\s+not|agrees\s+not\s+to)\s+(?:directly\s+or\s+indirectly\s+)?(?:compete|engage\s+in|provide\s+services\s+to\s+any\s+(?:competing|competitive)\s+business)',
        r'(?i)(?<!no\s)(?:non[\s\-]compete|noncompetition)(?:[^\.\n;]{0,120})(?:period\s+of|duration\s+of)\s+(?:[1-5]\s*years?|1[2-8]\s*months?|24\s*months?)',
        r'(?i)(?<!no\s)(?:compete\s+or\s+write\s+for|compete\s+with)(?:[^\.\n;]{0,120})(?:competing|competitive\s+business)'
    ],
    "asymmetric_liability": [
        r'(?i)(?:contractor|consultant|videographer|tester)\s+(?:shall|agrees\s+to)\s+(?:defend,\s+)?indemnify\s+and\s+hold\s+harmless(?:[^\.\n;]{0,200})(?:any\s+and\s+all\s+claims|losses|damages)',
        r'(?i)(?:without\s+limitation|uncapped|no\s+limitation\s+on\s+liability|unlimited\s+liability|with\s+uncapped\s+liability)',
        r'(?i)(?:in\s+no\s+event\s+shall\s+client\s+be\s+liable)(?:[^\.\n;]{0,150})(?:consequential|indirect|punitive|exceeding)'
    ],
    "unlimited_revisions": [
        r'(?i)(?:until\s+satisfied|until\s+the\s+deliverables\s+meet|until\s+the\s+app\s+satisfies)',
        r'(?i)(?:to\s+(?:the\s+)?(?:client(?:\'s)?|company(?:\'s)?)\s+sole\s+(?:satisfaction|discretion))',
        r'(?i)(?:unlimited\s+revisions|revisions\s+without\s+(?:additional\s+)?(?:fee|compensation|charge))',
        r'(?i)(?:revise|modify)\s+(?:all\s+)?deliverables\s+(?:until|as\s+many\s+times)',
        r'(?i)(?:produce\s+alternative\s+(?:creative\s+)?variations\s+until)'
    ],
    "termination_kill_fee": [
        r'(?i)(?:terminate|termination)\s+(?:at\s+will|for\s+convenience|without\s+cause)(?:[^\.\n;]{0,150})(?:without\s+(?:any\s+)?(?:further\s+payment|compensation|liability))',
        r'(?i)(?:no\s+kill\s+fee|no\s+cancellation\s+fee|no\s+payment\s+for\s+uncompleted\s+work)',
        r'(?i)(?:terminate\s+this\s+engagement\s+immediately\s+without\s+cause)',
        r'(?i)(?:immediate\s+termination|terminate\s+immediately\s+without\s+notice)'
    ],
    "late_payment_consequences": [
        r'(?i)(?:no\s+late\s+fee|no\s+interest\s+shall\s+accrue|interest-free|without\s+interest\s+or\s+penalty)',
        r'(?i)(?:under\s+no\s+circumstances\s+shall\s+(?:any\s+)?late\s+fee|no\s+penalty\s+for\s+late\s+payment)',
        r'(?i)(?:client|company)\s+may\s+withhold\s+(?:any\s+and\s+all\s+)?payments?\s+in\s+the\s+event\s+of\s+(?:any\s+)?dispute'
    ],
    "exclusivity": [
        r'(?i)(?:exclusive\s+basis|sole\s+and\s+exclusive\s+services?|exclusive\s+contractor)',
        r'(?i)(?:shall\s+not|prohibited\s+from)\s+(?:performing|providing)\s+services\s+to\s+any\s+other\s+(?:client|person|entity|company)',
        r'(?i)(?:work\s+on\s+an\s+exclusive\s+basis|shall\s+devote\s+full\s+time\s+and\s+efforts\s+solely)',
        r'(?i)(?:devote\s+full\s+time\s+and\s+efforts|refrain\s+from\s+outside\s+work)'
    ]
}

class ContractAnalyzer:
    """Orchestrates clause extraction across the 8 freelancer trap families."""

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama = ollama_client or OllamaClient()

    def analyze_contract(
        self,
        doc: ParsedDocument,
        force_mode: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> AnalysisReport:
        """
        Runs clause detection on the document.
        First tries local Ollama if available; falls back to deterministic engine.
        Applies Verifier to EVERY flag. Unverified quotes are dropped.
        """
        from .chunker import SectionChunker
        chunks = SectionChunker.split(doc)
        vector_index = InMemoryVectorIndex(chunks)

        ollama_active = self.ollama.is_available() and (force_mode != "deterministic")
        chosen_mode = "ollama_llm" if (ollama_active and force_mode != "deterministic") else "deterministic_baseline"
        
        flags: List[ClauseFlag] = []
        dropped: List[Dict[str, Any]] = []

        for family_key, defs in CLAUSE_DEFINITIONS.items():
            relevant_chunks = vector_index.search_by_family(family_key, top_k=3)
            context_text = "\n\n".join([f"[Page {c.page_number} - {c.section_title}]\n{c.text}" for c in relevant_chunks])

            flag_candidate: Optional[Dict[str, Any]] = None

            if chosen_mode == "ollama_llm":
                flag_candidate = self._detect_via_ollama(family_key, defs, context_text, model=model_name)

            # Fallback to deterministic regex/heuristic baseline if Ollama returns nothing or is offline
            if not flag_candidate or not flag_candidate.get("quote"):
                flag_candidate = self._detect_via_rules(family_key, doc, relevant_chunks)

            # Process candidate through the Verifier
            if flag_candidate and flag_candidate.get("quote"):
                raw_quote = flag_candidate["quote"]
                sug_page = flag_candidate.get("page")
                
                v_res: VerificationResult = ContractVerifier.verify_quote(raw_quote, doc, suggested_page=sug_page)
                
                if v_res.is_verified:
                    flags.append(ClauseFlag(
                        clause_id=f"flag_{family_key}",
                        clause_family=family_key,
                        family_label=defs["label"],
                        status="FLAGGED",
                        risk_level=flag_candidate.get("risk_level", defs["default_risk"]),
                        verbatim_quote=v_res.verbatim_quote,
                        page_number=v_res.page_number,
                        section_name=flag_candidate.get("section", "Contract Body"),
                        plain_english_explanation=flag_candidate.get("explanation", defs["description"]),
                        suggested_ask=flag_candidate.get("suggested_ask", defs["default_ask"]),
                        is_verified=True,
                        context_snippet=v_res.context_snippet,
                        origin=defs["origin"]
                    ))
                else:
                    # DROPPED to eliminate hallucination
                    dropped.append({
                        "family": family_key,
                        "raw_quote": raw_quote,
                        "drop_reason": v_res.drop_reason
                    })
                    # Add as NOT_DETECTED per specification rule
                    flags.append(ClauseFlag(
                        clause_id=f"flag_{family_key}",
                        clause_family=family_key,
                        family_label=defs["label"],
                        status="NOT_DETECTED",
                        risk_level="LOW",
                        plain_english_explanation="Not detected. Please verify manually.",
                        suggested_ask=defs["default_ask"],
                        is_verified=False,
                        origin=defs["origin"]
                    ))
            else:
                # Per Section 7: "if nothing is found for a clause family, the report says
                # 'Not detected. Please verify manually.' It never says 'no problems.'"
                flags.append(ClauseFlag(
                    clause_id=f"flag_{family_key}",
                    clause_family=family_key,
                    family_label=defs["label"],
                    status="NOT_DETECTED",
                    risk_level="LOW",
                    plain_english_explanation="Not detected. Please verify manually.",
                    suggested_ask=defs["default_ask"],
                    is_verified=False,
                    origin=defs["origin"]
                ))

        # Clear vector index from RAM immediately
        vector_index.clear()

        # Compute summary
        flagged_count = len([f for f in flags if f.status == "FLAGGED"])
        high_risk_count = len([f for f in flags if f.status == "FLAGGED" and f.risk_level == "HIGH"])
        
        used_model_label = model_name or ("Local Ollama" if chosen_mode == "ollama_llm" else "Deterministic Heuristic Engine")

        return AnalysisReport(
            filename=doc.filename,
            total_pages=doc.total_pages,
            flags=flags,
            dropped_hallucinations_count=len(dropped),
            unverified_flags_dropped=dropped,
            model_used=used_model_label,
            execution_mode=chosen_mode,
            summary={
                "total_clause_families_analyzed": len(CLAUSE_DEFINITIONS),
                "flagged_issues": flagged_count,
                "high_risk_issues": high_risk_count,
                "clean_or_unflagged": len(flags) - flagged_count,
                "verifier_rejections": len(dropped)
            }
        )

    def _detect_via_rules(
        self,
        family_key: str,
        doc: ParsedDocument,
        chunks: List[ContractChunk]
    ) -> Optional[Dict[str, Any]]:
        """High-precision regex/rule matching for baseline."""
        patterns = PATTERNS.get(family_key, [])
        defs = CLAUSE_DEFINITIONS[family_key]

        # Scan chunks first for precise section mapping
        for chunk in chunks:
            for pat in patterns:
                match = re.search(pat, chunk.text)
                if match:
                    span = match.group(0).strip()
                    # Expand span to full sentence
                    full_sentence = self._expand_to_sentence(chunk.text, match.start(), match.end())
                    return {
                        "quote": full_sentence or span,
                        "page": chunk.page_number,
                        "section": chunk.section_title,
                        "risk_level": defs["default_risk"],
                        "explanation": defs["description"],
                        "suggested_ask": defs["default_ask"]
                    }

        # Fallback scan across all document pages
        for page in doc.pages:
            for pat in patterns:
                match = re.search(pat, page.text)
                if match:
                    span = match.group(0).strip()
                    full_sentence = self._expand_to_sentence(page.text, match.start(), match.end())
                    return {
                        "quote": full_sentence or span,
                        "page": page.page_number,
                        "section": f"Page {page.page_number}",
                        "risk_level": defs["default_risk"],
                        "explanation": defs["description"],
                        "suggested_ask": defs["default_ask"]
                    }

        return None

    def _detect_via_ollama(
        self,
        family_key: str,
        defs: Dict[str, Any],
        context: str,
        model: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """LLM extraction chain for a specific clause family."""
        prompt = (
            f"You are a contract red-flag reviewer for freelancers analyzing clause family: {defs['label']}.\n"
            f"TARGET CRITERIA: {defs['description']}\n\n"
            f"Read the following contract excerpt:\n"
            f"\"\"\"\n{context[:3500]}\n\"\"\"\n\n"
            f"CRITICAL SAFETY RULE: You must quote the EXACT verbatim words from the excerpt. "
            f"Do not paraphrase or fabricate quotes. If no clause matching the target criteria is present, "
            f"respond with: {{\"detected\": false}}\n\n"
            f"If detected, return valid JSON with:\n"
            f"{{\n"
            f"  \"detected\": true,\n"
            f"  \"verbatim_quote\": \"<exact quote copied word for word>\",\n"
            f"  \"page\": <page number if known>,\n"
            f"  \"risk_level\": \"HIGH\" or \"MEDIUM\",\n"
            f"  \"plain_english_explanation\": \"<short plain english explanation of the trap>\",\n"
            f"  \"suggested_ask\": \"<what the freelancer should ask instead>\"\n"
            f"}}"
        )
        
        messages = [
            {"role": "system", "content": "You are VaultSign AI, an offline contract red-flag analyzer. Output JSON only."},
            {"role": "user", "content": prompt}
        ]

        resp = self.ollama.generate_chat(messages, model=model, temperature=0.0)
        if not resp:
            return None

        try:
            # Parse JSON from response
            cleaned = resp.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            data = json.loads(cleaned)
            
            if data.get("detected") and data.get("verbatim_quote"):
                return {
                    "quote": data["verbatim_quote"],
                    "page": data.get("page"),
                    "risk_level": data.get("risk_level", defs["default_risk"]),
                    "explanation": data.get("plain_english_explanation", defs["description"]),
                    "suggested_ask": data.get("suggested_ask", defs["default_ask"])
                }
        except Exception:
            pass

        return None

    def _expand_to_sentence(self, text: str, start: int, end: int) -> str:
        """Expands matched substring to sentence boundaries for readable quotes."""
        # Find start of sentence
        s = start
        while s > 0 and text[s-1] not in ".\n;":
            s -= 1
        # Find end of sentence
        e = end
        while e < len(text) and text[e] not in ".\n;":
            e += 1
        if e < len(text) and text[e] in ".;":
            e += 1
        candidate = text[s:e].strip()
        return candidate if len(candidate) <= 350 else text[start:end].strip()
