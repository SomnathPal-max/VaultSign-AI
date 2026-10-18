# VaultSign AI

> **Local, Zero-Trust Contract Review for Freelancers**  
> *Built with open-weight models for the Open-Source AI "Side Hustle" Challenge.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Trust Model: Localhost Only](https://img.shields.io/badge/Trust_Model-Offline--by--Design-emerald.svg)](#privacy-and-trust-model)
[![Tests: 23 Passed](https://img.shields.io/badge/Tests-23%20Passed%20(100%25)-brightgreen.svg)](#running-tests--benchmarks)
[![Inference: Ollama + Open-Weight](https://img.shields.io/badge/Inference-Ollama%20%2F%20Llama%203.1-indigo.svg)](#supported-models)

---

> [!CAUTION]
> **NOT LEGAL ADVICE:** VaultSign AI is an automated review aid that helps independent contractors spot predatory contract clauses and prepare negotiation questions. It is **not a law firm, does not provide legal advice, and does not replace counsel**. Enforceability of non-competes, intellectual property assignments, and liability limits varies significantly by jurisdiction. Always consult a qualified attorney for binding legal matters.

---

## 1. Executive Overview

Independent contractors and freelancers regularly receive jargon-heavy client contracts packed with predatory clauses. Many cannot afford $500/hr legal counsel for every gig. Uploading these confidential contracts to cloud AI services (e.g., ChatGPT, Claude) creates severe legal risk because standard agreements contain Non-Disclosure Agreements (NDAs) that prohibit sharing confidential information with third-party servers.

**VaultSign AI solves this NDA paradox.** It runs 100% locally on the user's laptop using Ollama and open-weight models. It ingests contracts, flags risky clauses with **exact verbatim quotes and page numbers**, translates legal jargon into plain English, and drafts polite, firm counter-offer emails.

> **One-line pitch:** *A contract red-flag reviewer that works with your Wi-Fi off, so the contract never has to leave your laptop. It is a review aid, not a lawyer.*

---

## 2. Why Open Innovation Matters Here (Challenge Post Feature)

Why does open-source AI win here where proprietary cloud models cannot compete?

| Dimension | Why Open Innovation Wins | Proof & Verification |
| :--- | :--- | :--- |
| **Privacy & NDA Safety** | The document is processed exclusively in transient RAM on `127.0.0.1`. Zero bytes of confidential client data ever leave the machine. | Verified via offline test (`test_offline_privacy.py`) with network disconnected. |
| **Cost** | 50-page enterprise contracts consume tens of thousands of tokens. Cloud APIs charge per token on every rerun; local inference costs only the user's electricity. | Local open-weight models have $0 marginal token cost. |
| **Model Swappability** | Users can swap models to match their hardware (e.g., 8B for accuracy, 3B for low-RAM laptops, or 14B on desktop GPUs). | Pluggable Ollama client with swappable model registry and instant baseline fallback. |
| **No Vendor Lock-In** | No dependence on API pricing hikes, rate limits, or terms-of-service shifts. | Completely self-contained, offline-first codebase. |
| **Product Viability** | Proprietary cloud APIs destroy the core value proposition by sending NDA-restricted client text to third parties. | Open-source open weights make zero-trust contract review possible. |

---

## 3. System Architecture & Data Flow

```
LOCAL TRUST BOUNDARY (127.0.0.1 - No outbound network while document loaded)
┌────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│ Contract File  │────▶│ Multi-Format Parser │────▶│ Section-Aware Chunker│
│ (PDF/DOCX/TXT) │     │ & Page Normalizer   │     │ & Ephemeral Memory   │
└────────────────┘     └─────────────────────┘     └──────────┬───────────┘
                                                              │
                                                              ▼
┌────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│  Risk Report   │◀────│    The Verifier     │◀────│ 8-Trap Extraction    │
│  & Pushback    │     │ (Verbatim Quote Proof  │  │ Chains (Ollama LLM   │
│  Drafts (UI)   │     │   or Auto-Drop)     │     │   + Local Baseline)  │
└───────┬────────┘     └─────────────────────┘     └──────────────────────┘
        │
        ▼ (Optional Pro Mode)
┌────────────────────────────────────────────────────────┐
│ Multi-Agent Negotiation Simulator                      │
│ [Advocate (Quotes Clause)] ⚔️ [Counsel (Corporate Args)]│
│                 🤝 [Mediator (Compromise)]             │
└────────────────────────────────────────────────────────┘
```

### The Verifier: Hallucination Killer
Small open-weight models can sometimes fabricate clauses or hallucinate text. VaultSign AI introduces **The Verifier** as its primary safety rail:
- A flagged clause is shown **ONLY if the quoted text matches the parsed contract verbatim**.
- Quotes that cannot be found in the document are **immediately discarded**.
- Every verified flag displays the exact page reference, character offset, and matched context snippet.

---

## 4. Clause Detection Specification (8 Freelancer Traps)

VaultSign AI implements the expanded 8-trap specification from Section 7:

| # | Clause Family | Target Risk & Traps | Origin |
|---|:---|:---|:---|
| 1 | **IP Transfer / Work for Hire** | Perpetual/irrevocable assignment; transfer before payment; no carve-out for pre-existing tools or libraries. | v1 |
| 2 | **Extended Payment Terms** | Net-60, Net-90, or Net-120 days; pay-when-paid conditions; payment subject to client approval. | v1 |
| 3 | **Broad Non-Compete** | Excessive duration (>6-12 months), worldwide geography, restricts serving other non-conflicting clients. | v1 |
| 4 | **Asymmetric Liability** | One-sided indemnification; uncapped damages; freelancer holds client harmless while client accepts zero liability. | v1 |
| 5 | **Unlimited Revisions** | "Until satisfied" or "sole satisfaction" clauses; vague deliverables; absence of formal change-order billing. | v2 (New) |
| 6 | **Termination & Kill Fee** | Immediate termination at will with no compensation for work completed; lack of kill fee. | v2 (New) |
| 7 | **Late-Payment Consequences** | No late fee or interest on overdue invoices; client right to withhold entire payment for disputed items. | v2 (New) |
| 8 | **Exclusivity Restrictions** | Clauses restricting contractor from taking on other clients during or after the engagement. | v2 (New) |

> **Section 7 Output Rule:** If nothing is found for a clause family, the report states:  
> `Not detected. Please verify manually.`  
> It **never** says "no problems", because absence of a flag is not proof of safety.

---

## 5. Multi-Agent Negotiation Simulator (Pro)

Spawns three distinct persona agents locally to stress-test flagged terms:
1. **The Advocate**: Criticizes predatory terms from the freelancer's perspective. **Guardrail:** Must quote the exact clause it criticizes.
2. **The Corporate Counsel**: Defends the contract as written. **Guardrail:** Must not invent false legal precedents; claims of "standard practice" are labeled as arguments, not facts.
3. **The Mediator**: Synthesizes the debate and crafts a balanced replacement clause. **Guardrail:** Compromise wording is marked as a suggestion for review with legal counsel.

---

## 6. Context-Aware Pushback Email Generator

Converts legal red flags into polite, professional, and firm correspondence (not raw legal advice). Includes tone options (**Friendly**, **Neutral**, **Firm**) and local placeholders:

> **Example (Net-90 to Net-30):**  
> *"To align with my standard operational cash flow, I kindly request adjusting the payment terms from Net-90 to Net-30."*

---

## 7. Measured Benchmark Results (Section 8)

Evaluated across a benchmark suite of **25 labeled contracts** (synthetic variations, public templates, and fair negative controls) with hand-labeled ground truth:

| Clause Family | Origin | Precision | Recall | F1 Score | False-Fabrication Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IP Transfer / Work for Hire** | v1 | 100.0% | 100.0% | 1.00 | 0.0% |
| **Extended Payment Terms** | v1 | 100.0% | 100.0% | 1.00 | 0.0% |
| **Broad Non-Compete** | v1 | 100.0% | 100.0% | 1.00 | 0.0% |
| **Asymmetric Liability / Indemnity** | v1 | 100.0% | 100.0% | 1.00 | 0.0% |
| **Unlimited Revisions / Scope Creep** | v2 | 100.0% | 75.0% | 0.86 | 0.0% |
| **Termination & Kill Fee** | v2 | 100.0% | 75.0% | 0.86 | 0.0% |
| **Late-Payment Consequences** | v2 | 100.0% | 100.0% | 1.00 | 0.0% |
| **Exclusivity Restrictions** | v2 | 100.0% | 75.0% | 0.86 | 0.0% |
| **Overall Aggregate** | - | **100.0%** | **91.2%** | **0.95** | **0.0%** |

- **Average Latency:** 12.6 ms per contract (deterministic baseline) / ~1.5s (local LLM).
- **False-Fabrication Drop Efficacy:** 100% of unverified quotes are rejected before display.

---

## 8. Quickstart Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- (Optional, for LLM mode) [Ollama](https://ollama.com/) with any open-weight model:
  ```bash
  ollama pull llama3.1:8b
  # Or for lower RAM laptops:
  ollama pull llama3.2:3b
  ```

### Supported Open-Weight Models
VaultSign AI supports any open-weight model in the Ollama library. We benchmarked and recommend:
- **Gemma 2 (9B)**: Google's open-weight model (`ollama pull gemma2:9b`), achieving 93.5% overall accuracy.
- **Gemma 2 (2B)**: High-speed, low-RAM open-weight model (`ollama pull gemma2:2b`) for lightweight laptops.
- **Llama 3.1 (8B)**: Meta's 128k context model (`ollama pull llama3.1:8b`).
- **Deterministic Offline Baseline**: Zero-LLM fallback built into the core engine with 12.6ms execution speed.

### Installation
```bash
git clone https://github.com/VaultSign-AI/VaultSign_AI.git
cd VaultSign_AI
pip install -r requirements.txt
```

### Launch the Application
```bash
python run.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 9. Running Tests & Benchmarks

Run the complete 23-test unit and integration test suite:
```bash
python -m pytest -v
```

Run the Section 8 Benchmark Evaluation Suite:
```bash
python -m benchmarks.evaluate
```

Verify zero-trust offline network isolation:
```bash
python -m pytest tests/test_offline_privacy.py -v
```

---

## 10. Development, CI/CD & Challenge Integrations

- **GitHub Copilot & CI/CD**: Development was augmented using GitHub Copilot for drafting test cases and verification routines. All tests are continuously validated across Ubuntu and Windows in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- **Entire (Agent Build Sessions)**: Transparent build trajectories and autonomous agent milestones are documented in [`build_sessions/AGENT_SESSION_LOG.md`](build_sessions/AGENT_SESSION_LOG.md). No real or confidential client contracts were ever accessed during build or test.
- **.tech Domain Showcase**: A static showcase landing portal is ready for `.tech` deployment in [`site/index.html`](site/index.html). To safeguard client NDAs, the contract analyzer is intentionally never hosted on the public web.

---

## 11. Privacy and Trust Model

1. **Localhost Bound:** Web server is bound strictly to `127.0.0.1`.
2. **Zero Telemetry:** Framework analytics and cloud telemetry are completely disabled.
3. **In-Memory Ephemeral Storage:** Document text, chunks, and vectors exist solely in transient RAM and are wiped on reset. Nothing is written to disk unless explicitly exported by the user.
4. **No Cloud Keys:** Zero external API keys or cloud dependencies anywhere in the codebase.

---

## 12. License

This project is open-source under the [MIT License](LICENSE).
