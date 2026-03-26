"""DocuGen AI – Document generation and summarisation routes."""
import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.services.docgen_service import DocGenService, get_docgen_service

router = APIRouter(prefix="/documents", tags=["Document Generation"])

SUPPORTED_TYPES = ["executive_summary", "technical_report", "business_proposal", "meeting_notes"]


class GenerateRequest(BaseModel):
    query: str
    doc_type: str = "executive_summary"
    llm_provider: str = "claude"


class SummariseRequest(BaseModel):
    text: str
    style: str = "concise"


@router.post("/generate")
async def generate_document(
    request: GenerateRequest,
    service: DocGenService = Depends(get_docgen_service),
):
    """Generate a structured document from the indexed knowledge base."""
    if request.doc_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown doc_type '{request.doc_type}'. Choose from: {SUPPORTED_TYPES}",
        )
    if request.llm_provider not in ("claude", "mistral"):
        raise HTTPException(status_code=400, detail="llm_provider must be 'claude' or 'mistral'")
    return service.generate_document(request.query, request.doc_type, request.llm_provider)


@router.post("/summarise")
async def summarise_text(
    request: SummariseRequest,
    service: DocGenService = Depends(get_docgen_service),
):
    """Summarise provided text in the requested style."""
    if len(request.text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short to summarise (min 50 characters).")
    return service.summarise(request.text, request.style)


@router.post("/upload")
async def upload_source_documents(
    files: List[UploadFile] = File(...),
    service: DocGenService = Depends(get_docgen_service),
):
    """Upload source documents for knowledge base ingestion."""
    supported_extensions = (".pdf", ".txt", ".md", ".docx")
    saved_paths = []
    tmp_dir = tempfile.mkdtemp()
    try:
        for file in files:
            if not any(file.filename.endswith(ext) for ext in supported_extensions):
                raise HTTPException(status_code=400, detail=f"Unsupported: {file.filename}")
            dest = Path(tmp_dir) / file.filename
            with open(dest, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_paths.append(str(dest))

        result = service.ingest_documents(saved_paths)
        result["files"] = [f.filename for f in files]
        return result
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("/templates")
async def list_templates():
    return {"templates": SUPPORTED_TYPES}


@router.get("/stats")
async def get_stats(service: DocGenService = Depends(get_docgen_service)):
    return service.get_stats()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "DocuGen AI - Intelligent Document Generation"}
