"""
VaultSign AI - Section-Aware Chunker & In-Memory Ephemeral Vector Index
Splits contracts by structural legal sections (preserving definitions and cross-references)
and provides in-memory vector search with zero disk persistence.
"""

import re
import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .parser import ParsedDocument, ParsedPage

class ContractChunk(BaseModel):
    chunk_id: str
    section_title: str
    page_number: int
    text: str
    char_start: int
    char_end: int
    is_definition_block: bool = False

SECTION_PATTERNS = [
    # E.g. "SECTION 1. INTELLECTUAL PROPERTY" or "Section 2.3: Payment"
    r'(?im)^(?:\s*(?:SECTION|ARTICLE|CLAUSE|PARAGRAPH)\s+([0-9IVXLCDM\.\-]+)[:\.\s\-]+([^\n\r]+))',
    # E.g. "1. SCOPE OF SERVICES" or "2. PAYMENT TERMS"
    r'(?im)^(?:\s*([0-9]{1,2}\.[0-9]{0,2})\s+([A-Z][A-Za-z0-9\s,\-_&/]{2,60}))',
    # E.g. "RECITALS", "DEFINITIONS", "INDEMNIFICATION", "CONFIDENTIALITY"
    r'(?im)^(?:\s*([A-Z\s]{4,40})\s*)$'
]

COMMON_CLAUSE_TOPICS = {
    "ip": ["intellectual property", "inventions", "work made for hire", "assignment of rights", "proprietary rights", "copyright", "ownership"],
    "payment": ["payment terms", "compensation", "invoicing", "fees", "net 30", "net 60", "net 90", "expenses", "remuneration"],
    "non_compete": ["non-compete", "non-competition", "restrictive covenants", "competitive business", "restraint of trade"],
    "liability": ["indemnification", "indemnity", "hold harmless", "limitation of liability", "damages", "liable"],
    "revisions": ["revisions", "scope of work", "acceptance", "satisfaction", "change order", "deliverables", "review period"],
    "termination": ["termination", "term and termination", "kill fee", "early termination", "notice of cancellation", "default"],
    "late_payment": ["late fee", "interest on overdue", "disputed payments", "past due", "withhold payment"],
    "exclusivity": ["exclusivity", "exclusive services", "conflict of interest", "outside activities", "other clients"]
}

class SectionChunker:
    """Splits contract into section-aware chunks that preserve legal context."""
    
    @staticmethod
    def split(doc: ParsedDocument) -> List[ContractChunk]:
        chunks: List[ContractChunk] = []
        chunk_idx = 0

        # Process page by page while maintaining section continuity
        current_section = "Preamble / General Terms"
        
        for page in doc.pages:
            lines = page.text.split("\n")
            current_buffer: List[str] = []
            char_offset = page.char_start

            for line in lines:
                is_heading = False
                detected_heading = None

                for pat in SECTION_PATTERNS:
                    match = re.match(pat, line.strip())
                    if match:
                        groups = match.groups()
                        detected_heading = " - ".join([g for g in groups if g]).strip()
                        is_heading = True
                        break

                if is_heading and detected_heading:
                    # Flush current buffer into a chunk
                    if current_buffer:
                        text_chunk = "\n".join(current_buffer).strip()
                        if len(text_chunk) > 40:
                            is_def = "definition" in current_section.lower() or "defined terms" in current_section.lower()
                            chunks.append(ContractChunk(
                                chunk_id=f"c_{chunk_idx}",
                                section_title=current_section,
                                page_number=page.page_number,
                                text=text_chunk,
                                char_start=char_offset,
                                char_end=char_offset + len(text_chunk),
                                is_definition_block=is_def
                            ))
                            chunk_idx += 1
                        current_buffer = []

                    current_section = detected_heading
                    current_buffer.append(line)
                else:
                    current_buffer.append(line)
                    
                    # Split if chunk gets overly long (> 1800 chars) while avoiding split mid-sentence
                    if len("\n".join(current_buffer)) > 1800 and (line.endswith(".") or line.endswith(";")):
                        text_chunk = "\n".join(current_buffer).strip()
                        is_def = "definition" in current_section.lower() or "defined terms" in current_section.lower()
                        chunks.append(ContractChunk(
                            chunk_id=f"c_{chunk_idx}",
                            section_title=current_section,
                            page_number=page.page_number,
                            text=text_chunk,
                            char_start=char_offset,
                            char_end=char_offset + len(text_chunk),
                            is_definition_block=is_def
                        ))
                        chunk_idx += 1
                        current_buffer = []

            # Flush remaining buffer for this page
            if current_buffer:
                text_chunk = "\n".join(current_buffer).strip()
                if len(text_chunk) > 30:
                    is_def = "definition" in current_section.lower() or "defined terms" in current_section.lower()
                    chunks.append(ContractChunk(
                        chunk_id=f"c_{chunk_idx}",
                        section_title=current_section,
                        page_number=page.page_number,
                        text=text_chunk,
                        char_start=char_offset,
                        char_end=char_offset + len(text_chunk),
                        is_definition_block=is_def
                    ))
                    chunk_idx += 1

        # Fallback if no sections were parsed
        if not chunks and doc.full_text:
            chunks.append(ContractChunk(
                chunk_id="c_0",
                section_title="Full Document",
                page_number=1,
                text=doc.full_text[:3000],
                char_start=0,
                char_end=len(doc.full_text)
            ))

        return chunks


class InMemoryVectorIndex:
    """
    Transient, in-memory semantic search and BM25-style relevance ranking index.
    Zero disk persistence: everything exists in RAM and is wiped on reset.
    """
    def __init__(self, chunks: List[ContractChunk]):
        self.chunks = chunks
        self.doc_tokens: List[List[str]] = [self._tokenize(c.text + " " + c.section_title) for c in chunks]
        self.vocab: Dict[str, int] = {}
        self.df: Dict[str, int] = {}
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'[A-Za-z0-9_\-]+', text) if len(w) > 2]

    def _build_index(self):
        for tokens in self.doc_tokens:
            unique_terms = set(tokens)
            for t in unique_terms:
                self.df[t] = self.df.get(t, 0) + 1

    def search(self, query: str, top_k: int = 5, min_score: float = 0.05) -> List[ContractChunk]:
        """In-memory TF-IDF / BM25 style relevance score for matching chunks."""
        q_tokens = self._tokenize(query)
        if not q_tokens or not self.chunks:
            return self.chunks[:top_k]

        N = len(self.chunks)
        scores = []

        for idx, tokens in enumerate(self.doc_tokens):
            score = 0.0
            doc_len = max(len(tokens), 1)
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

            for q in q_tokens:
                if q in token_counts:
                    tf = token_counts[q] / doc_len
                    idf = math.log((N + 1) / (self.df.get(q, 0) + 0.5)) + 1.0
                    score += tf * idf

            # Bonus for section title match
            sec_title_lower = self.chunks[idx].section_title.lower()
            for q in q_tokens:
                if q in sec_title_lower:
                    score += 0.8

            scores.append((score, self.chunks[idx]))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = [chunk for score, chunk in scores if score >= min_score][:top_k]
        
        # If no score meets threshold, return top 2 as fallback
        return results if results else [c for _, c in scores[:min(2, len(scores))]]

    def search_by_family(self, family_key: str, top_k: int = 4) -> List[ContractChunk]:
        """Retrieve chunks most relevant to a specific clause family."""
        keywords = COMMON_CLAUSE_TOPICS.get(family_key, [family_key])
        query = " ".join(keywords)
        return self.search(query, top_k=top_k)

    def clear(self):
        """Immediately clear all chunk and token references from memory."""
        self.chunks.clear()
        self.doc_tokens.clear()
        self.vocab.clear()
        self.df.clear()
