from fastapi import APIRouter, Depends, HTTPException, Request

from normen_tool.api.dependencies import get_project_context
from normen_tool.api.project_manager import open_project
from normen_tool.api.schemas import (
    ProjectOpenRequest,
    ProjectOpenResponse,
    ProjectStatusResponse,
    PDFListResponse,
)
from normen_tool.api.utils import document_to_pdf_metadata

router = APIRouter(prefix="/project", tags=["project"])


@router.post("/open", response_model=ProjectOpenResponse)
def open_project_endpoint(request: Request, request_body: ProjectOpenRequest):
    try:
        context = open_project(request.app, request_body.project_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    status = "created" if context.created else "loaded"
    return {
        "project_dir": str(context.project_dir),
        "db_file": str(context.db_file),
        "status": status,
        "message": f"Project {status} successfully.",
    }


@router.get("/status", response_model=ProjectStatusResponse)
def get_project_status(context=Depends(get_project_context)):
    statistics = context.db_client.get_statistics()
    return {
        "project_dir": str(context.project_dir),
        "db_file": str(context.db_file),
        "db_exists": context.db_file.exists() if context.db_file else False,
        "pdf_count": statistics["documents"],
        "document_count": statistics["documents"],
        "block_count": statistics["blocks"],
    }


@router.get("/pdfs", response_model=PDFListResponse)
def list_project_pdfs(context=Depends(get_project_context)):
    documents = context.db_client.list_documents()
    return {
        "pdfs": [document_to_pdf_metadata(doc) for doc in documents],
        "count": len(documents),
    }
