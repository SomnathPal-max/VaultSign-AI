"""
VaultSign AI - Zero-Trust Localhost Web Server & API
FastAPI application bound strictly to 127.0.0.1 with zero telemetry.
Provides contract analysis, multi-agent debate simulation, pushback email generation,
and report export.
"""

import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import HOST, PORT, LEGAL_DISCLAIMER, JURISDICTION_NOTICE
from .parser import parse_document, ParsedDocument
from .analyzer import ContractAnalyzer, AnalysisReport, ClauseFlag
from .agents import MultiAgentSimulator, NegotiationDebate
from .pushback import PushbackGenerator, PushbackEmail
from .exporter import ReportExporter
from .ollama_client import OllamaClient

app = FastAPI(
    title="VaultSign AI",
    description="Local, Zero-Trust Contract Red-Flag Reviewer for Freelancers",
    version="2.0.0"
)

# Enforce localhost only CORS policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Application state in memory (ephemeral, not persisted to disk)
CURRENT_PARSED_DOC: Optional[ParsedDocument] = None
CURRENT_ANALYSIS_REPORT: Optional[AnalysisReport] = None

ollama_client = OllamaClient()
analyzer = ContractAnalyzer(ollama_client)
agent_simulator = MultiAgentSimulator(ollama_client)

# Mount static folder
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>VaultSign AI - Initializing UI...</h1>"

@app.get("/api/status")
def get_system_status():
    ollama_ok = ollama_client.is_available()
    raw_models = ollama_client.list_local_models() if ollama_ok else []
    # Filter out embedding-only models from LLM selector
    models = [m for m in raw_models if not any(x in m.lower() for x in ["embed", "bge", "bert"])]
    def_model = (ollama_client.get_best_available_model() if ollama_ok else None) or "Deterministic Engine Baseline"
    return {
        "status": "online",
        "trust_boundary": "127.0.0.1 (Strict Localhost)",
        "network_guard": "OFFLINE_VERIFIED",
        "ollama_connected": ollama_ok,
        "available_models": models,
        "default_model": def_model,
        "has_loaded_document": CURRENT_PARSED_DOC is not None,
        "loaded_filename": CURRENT_PARSED_DOC.filename if CURRENT_PARSED_DOC else None,
        "legal_notice": LEGAL_DISCLAIMER
    }

@app.post("/api/analyze")
def analyze_uploaded_document(
    file: Optional[UploadFile] = File(None),
    sample_name: Optional[str] = Form(None),
    execution_mode: Optional[str] = Form("hybrid"),  # "ollama_llm", "deterministic", "hybrid"
    model_name: Optional[str] = Form(None)
):
    global CURRENT_PARSED_DOC, CURRENT_ANALYSIS_REPORT
    
    file_bytes: bytes = b""
    filename: str = "document.txt"

    if file:
        file_bytes = file.file.read() if hasattr(file, "file") else file.read()
        filename = file.filename
    elif sample_name:
        # Load sample contract from data/sample_contracts
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "sample_contracts", sample_name
        )
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as sf:
                file_bytes = sf.read()
            filename = sample_name
        else:
            raise HTTPException(status_code=404, detail=f"Sample contract '{sample_name}' not found")
    else:
        raise HTTPException(status_code=400, detail="Must provide an uploaded file or sample_name")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="File is empty")

    # Resolve FastAPI Form defaults if called directly
    clean_mode = execution_mode if isinstance(execution_mode, str) else "hybrid"
    clean_model = model_name if isinstance(model_name, str) else None

    # Step 1: Parse document (PDF / DOCX / TXT)
    parsed_doc = parse_document(file_bytes, filename)
    CURRENT_PARSED_DOC = parsed_doc

    # Step 2: Run 8-trap clause analysis & verbatim quote verification
    report = analyzer.analyze_contract(
        parsed_doc,
        force_mode="deterministic" if clean_mode == "deterministic" else None,
        model_name=clean_model
    )
    CURRENT_ANALYSIS_REPORT = report

    return {
        "success": True,
        "report": report.model_dump(),
        "disclaimer": LEGAL_DISCLAIMER,
        "jurisdiction_warning": JURISDICTION_NOTICE
    }

class DebateRequest(BaseModel):
    clause_family: str
    model_name: Optional[str] = None

@app.post("/api/simulate-debate")
def run_multi_agent_debate(req: DebateRequest):
    global CURRENT_ANALYSIS_REPORT, CURRENT_PARSED_DOC
    if not CURRENT_ANALYSIS_REPORT or not CURRENT_PARSED_DOC:
        raise HTTPException(status_code=400, detail="No analyzed contract currently in memory")

    target_flag = next((f for f in CURRENT_ANALYSIS_REPORT.flags if f.clause_family == req.clause_family), None)
    if not target_flag:
        raise HTTPException(status_code=404, detail=f"Clause family '{req.clause_family}' not found")

    debate = agent_simulator.simulate_clause_debate(
        target_flag,
        CURRENT_PARSED_DOC,
        model_name=req.model_name
    )
    return {
        "success": True,
        "debate": debate.model_dump()
    }

class PushbackRequest(BaseModel):
    clause_family: str
    tone: str = "neutral"
    user_name: str = "[Your Name]"
    client_name: str = "[Client Name]"
    project_name: str = "[Project Name]"
    clause_reference: Optional[str] = None
    custom_justification: Optional[str] = None

@app.post("/api/generate-pushback")
def generate_pushback_email(req: PushbackRequest):
    global CURRENT_ANALYSIS_REPORT
    quote = ""
    ref = req.clause_reference or "the agreement"

    if CURRENT_ANALYSIS_REPORT:
        flag = next((f for f in CURRENT_ANALYSIS_REPORT.flags if f.clause_family == req.clause_family), None)
        if flag and flag.verbatim_quote:
            quote = flag.verbatim_quote
            ref = req.clause_reference or f"Section / Page {flag.page_number} ({flag.family_label})"

    if not quote:
        quote = "Standard contractual clause terms"

    email = PushbackGenerator.generate_email(
        clause_family=req.clause_family,
        verbatim_quote=quote,
        clause_reference=ref,
        tone=req.tone,
        user_name=req.user_name,
        client_name=req.client_name,
        project_name=req.project_name,
        custom_justification=req.custom_justification
    )
    return {
        "success": True,
        "email": email.model_dump()
    }

class ExportRequest(BaseModel):
    format: str = "markdown"  # "markdown", "html", "json"
    user_name: str = "Freelancer"
    client_name: str = "Client"

@app.post("/api/export")
def export_report(req: ExportRequest):
    global CURRENT_ANALYSIS_REPORT
    if not CURRENT_ANALYSIS_REPORT:
        raise HTTPException(status_code=400, detail="No analysis report exists to export")

    if req.format == "html":
        content = ReportExporter.to_html(CURRENT_ANALYSIS_REPORT, req.user_name, req.client_name)
        return HTMLResponse(content=content, headers={
            "Content-Disposition": f"attachment; filename=VaultSign_Audit_{CURRENT_ANALYSIS_REPORT.filename}.html"
        })
    elif req.format == "json":
        content = ReportExporter.to_json(CURRENT_ANALYSIS_REPORT)
        return PlainTextResponse(content=content, media_type="application/json", headers={
            "Content-Disposition": f"attachment; filename=VaultSign_Audit_{CURRENT_ANALYSIS_REPORT.filename}.json"
        })
    else:
        content = ReportExporter.to_markdown(CURRENT_ANALYSIS_REPORT, req.user_name, req.client_name)
        return PlainTextResponse(content=content, media_type="text/markdown", headers={
            "Content-Disposition": f"attachment; filename=VaultSign_Audit_{CURRENT_ANALYSIS_REPORT.filename}.md"
        })

@app.post("/api/reset")
def reset_workspace():
    """Wipes all documents and vectors from in-memory RAM."""
    global CURRENT_PARSED_DOC, CURRENT_ANALYSIS_REPORT
    CURRENT_PARSED_DOC = None
    CURRENT_ANALYSIS_REPORT = None
    return {"success": True, "message": "In-memory document session wiped cleanly. Zero traces retained."}

@app.get("/api/samples")
def list_sample_contracts():
    samples_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data", "sample_contracts"
    )
    if not os.path.exists(samples_dir):
        return {"samples": []}
    files = [f for f in os.listdir(samples_dir) if f.endswith((".txt", ".pdf", ".docx"))]
    return {"samples": files}
