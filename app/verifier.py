"""
VaultSign AI - The Verifier Engine
The core safety mechanism: every flagged clause MUST match the parsed contract
verbatim (or normalized text). Quotes that cannot be verified are dropped to
eliminate LLM hallucinations and fabricated clauses.
"""

import re
from typing import Optional, Tuple, Dict, Any, List
from pydantic import BaseModel
from .parser import ParsedDocument, ParsedPage

class VerificationResult(BaseModel):
    is_verified: bool
    verbatim_quote: str
    matched_text: Optional[str] = None
    page_number: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    context_snippet: Optional[str] = None
    drop_reason: Optional[str] = None

class ContractVerifier:
    """Verifies that an extracted quote exists verbatim in the contract source."""

    @staticmethod
    def _clean_quote_str(text: str) -> str:
        """Strip surrounding quotes, Markdown backticks, and normalize spaces."""
        text = text.strip()
        text = re.sub(r'^["\'`“]+|["\'`”]+$', '', text)
        return text.strip()

    @staticmethod
    def _normalize_tokens(text: str) -> str:
        """Normalize spaces, punctuation nuances, and line breaks for matching."""
        # Replace dashes, smart quotes, ligatures
        t = text.replace("’", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
        # Collapse multiple whitespace
        return re.sub(r'\s+', ' ', t).strip()

    @classmethod
    def verify_quote(
        cls,
        quote: str,
        doc: ParsedDocument,
        suggested_page: Optional[int] = None
    ) -> VerificationResult:
        """
        Validates quote against the document.
        Returns VerificationResult with exact page and offsets, or drop reason.
        """
        clean_q = cls._clean_quote_str(quote)
        if not clean_q or len(clean_q) < 8:
            return VerificationResult(
                is_verified=False,
                verbatim_quote=quote,
                drop_reason="Quote is too short or empty to verify reliably"
            )

        norm_q = cls._normalize_tokens(clean_q).lower()

        # Step 1: Check suggested page first if provided (safe int conversion)
        page_idx: Optional[int] = None
        if suggested_page is not None:
            try:
                page_idx = int(suggested_page)
            except (ValueError, TypeError):
                page_idx = None

        pages_to_check: List[ParsedPage] = []
        if page_idx and 1 <= page_idx <= len(doc.pages):
            pages_to_check.append(doc.pages[page_idx - 1])
        # Then append all other pages
        for p in doc.pages:
            if not page_idx or p.page_number != page_idx:
                pages_to_check.append(p)

        # Step 2: Exact verbatim substring check
        for page in pages_to_check:
            page_text = page.text
            if clean_q in page_text:
                idx = page_text.index(clean_q)
                start_char = page.char_start + idx
                end_char = start_char + len(clean_q)
                
                # Context snippet (30 chars before and after)
                ctx_start = max(0, idx - 40)
                ctx_end = min(len(page_text), idx + len(clean_q) + 40)
                snippet = page_text[ctx_start:ctx_end].replace("\n", " ")

                return VerificationResult(
                    is_verified=True,
                    verbatim_quote=clean_q,
                    matched_text=clean_q,
                    page_number=page.page_number,
                    char_start=start_char,
                    char_end=end_char,
                    context_snippet=snippet
                )

        # Step 3: Normalized substring check (handling line breaks and spacing variations)
        for page in pages_to_check:
            page_norm = cls._normalize_tokens(page.text).lower()
            if norm_q in page_norm:
                # Find best matching original slice in page
                words = norm_q.split()
                if words:
                    first_word = re.escape(words[0])
                    last_word = re.escape(words[-1])
                    pattern = rf'(?i){first_word}.*?{last_word}'
                    match = re.search(pattern, page.text, re.DOTALL)
                    if match:
                        matched_span = match.group(0)
                        idx = match.start()
                        start_char = page.char_start + idx
                        end_char = page.char_start + match.end()
                        ctx_start = max(0, idx - 40)
                        ctx_end = min(len(page.text), match.end() + 40)
                        snippet = page.text[ctx_start:ctx_end].replace("\n", " ")

                        return VerificationResult(
                            is_verified=True,
                            verbatim_quote=matched_span,
                            matched_text=matched_span,
                            page_number=page.page_number,
                            char_start=start_char,
                            char_end=end_char,
                            context_snippet=snippet
                        )

        # Step 4: Fallback to full document text check
        full_norm = cls._normalize_tokens(doc.full_text).lower()
        if norm_q in full_norm:
            # Locate which page contains this match
            cumulative = 0
            for page in doc.pages:
                if norm_q[:min(30, len(norm_q))] in cls._normalize_tokens(page.text).lower():
                    return VerificationResult(
                        is_verified=True,
                        verbatim_quote=clean_q,
                        matched_text=clean_q,
                        page_number=page.page_number,
                        context_snippet=page.text[:120].replace("\n", " ")
                    )

        # If not found anywhere, DISCARD (DROP)
        return VerificationResult(
            is_verified=False,
            verbatim_quote=quote,
            drop_reason="Quote could not be found verbatim in contract. Dropped to eliminate fabricated clause."
        )
