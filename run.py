"""
VaultSign AI - Runner Script
Launches the zero-trust local server on 127.0.0.1:8000.
"""

import sys
import uvicorn
from app.config import HOST, PORT

def main():
    print("=" * 65)
    print(" VaultSign AI - Zero-Trust Local Contract Reviewer")
    print(" Open-Source AI Side Hustle Challenge")
    print("=" * 65)
    print(f"[*] Bound strictly to localhost: http://{HOST}:{PORT}")
    print("[*] Privacy Mode: OFFLINE-BY-DESIGN (Zero outbound network traffic)")
    print("[*] Document Storage: EPHEMERAL IN-MEMORY ONLY")
    print("[*] Press Ctrl+C to terminate server safely.")
    print("=" * 65)
    
    uvicorn.run("app.server:app", host=HOST, port=PORT, log_level="info")

if __name__ == "__main__":
    main()
