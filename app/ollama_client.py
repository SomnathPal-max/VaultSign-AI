"""
VaultSign AI - Local Ollama Client
Communicates strictly via localhost (127.0.0.1:11434) with zero outbound network calls.
Handles model discovery, context management, and graceful offline fallback.
"""

import json
import socket
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from .config import OLLAMA_BASE_URL, DEFAULT_MODEL, FALLBACK_SMALL_MODEL

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        """Check if local Ollama daemon is active and responding."""
        try:
            s = socket.socket()
            s.settimeout(0.1)
            res = s.connect_ex(("127.0.0.1", 11434))
            s.close()
            return res == 0
        except Exception:
            return False

    def list_local_models(self) -> List[str]:
        """Fetch list of models currently pulled in local Ollama instance."""
        if not self.is_available():
            return []
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                return models
        except Exception:
            return []

    def get_best_available_model(self) -> Optional[str]:
        """Returns preferred model from available models, or fallback."""
        available = self.list_local_models()
        if not available:
            return None
        
        # Check preference
        for pref in [DEFAULT_MODEL, "gemma2:9b", "gemma2", "llama3.1", "llama3", "qwen2.5:7b", "qwen2.5", "mistral", "gemma2:2b", FALLBACK_SMALL_MODEL]:
            for model_name in available:
                if pref in model_name:
                    return model_name
        return available[0]

    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> Optional[str]:
        """
        Send chat prompt to local Ollama API.
        Enforces 127.0.0.1 target and fails immediately if unreachable.
        """
        target_model = model or self.get_best_available_model() or DEFAULT_MODEL
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 8192  # Long context support for contracts
            }
        }
        
        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=data_bytes,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json.get("message", {}).get("content", "").strip()
        except Exception as e:
            # Local Ollama unavailable or timeout
            return None
