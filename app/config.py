"""
VaultSign AI - Configuration & Privacy Guardrails
Local, Zero-Trust Contract Review for Freelancers
"""

import os
from pydantic import BaseModel

# Server & Privacy Configuration
HOST = "127.0.0.1"  # Bound strictly to localhost
PORT = 8000
DEBUG = False

# Strict Zero-Trust & Offline Mode
NETWORK_GUARD_ENABLED = True
ALLOW_OUTBOUND_NETWORK = False  # Refuses outbound HTTP/HTTPS calls when document loaded
IN_MEMORY_ONLY = True           # Never persist vector index or parsed text to disk

# LLM & Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = "llama3.1:8b"
FALLBACK_SMALL_MODEL = "llama3.2:3b"
SUPPORTED_MODELS = [
    "gemma2:9b",
    "gemma2:2b",
    "llama3.1:8b",
    "llama3.2:3b",
    "llama3:8b",
    "qwen2.5:7b",
    "qwen2.5:3b",
    "mistral:7b",
    "phi3:mini"
]

# Legal & Safety Notice
LEGAL_DISCLAIMER = (
    "NOT LEGAL ADVICE: VaultSign AI is an automated review aid designed to help freelancers "
    "identify potential red flags and prepare negotiating questions. It is not a law firm and "
    "does not provide legal advice or legal representation. Contract enforceability varies "
    "significantly by jurisdiction. Always consult a qualified attorney for binding legal matters."
)

JURISDICTION_NOTICE = (
    "Jurisdiction Warning: Enforceability of non-compete restrictions, intellectual property "
    "assignments, and liability waivers depends heavily on applicable state, national, or local laws "
    "(e.g., California FTC non-compete bans vs other jurisdictions). Always check local rules."
)

class AppSettings(BaseModel):
    host: str = HOST
    port: int = PORT
    ollama_url: str = OLLAMA_BASE_URL
    default_model: str = DEFAULT_MODEL
    network_guard: bool = NETWORK_GUARD_ENABLED
    in_memory_only: bool = IN_MEMORY_ONLY
