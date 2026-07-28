"""Pydantic schemas for API requests and responses."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ========== Project Schemas ==========

class ProjectStatusResponse(BaseModel):
    """Response for GET /project/status."""

    project_dir: str
    db_file: str
    db_exists: bool
    pdf_count: int
    document_count: int
    block_count: int


class ProjectOpenRequest(BaseModel):
    """Request for POST /project/open."""

    project_dir: str = Field(..., description="Path to project folder containing PDFs")


class ProjectOpenResponse(BaseModel):
    """Response for POST /project/open."""

    project_dir: str
    db_file: str
    status: str  # "created" or "loaded"
    message: str


# ========== PDF Schemas ==========

class PDFMetadata(BaseModel):
    """Metadata for a PDF document."""

    id: str
    name: str
    path: str
    page_count: int
    has_text_layer: bool
    created_at: datetime
    modified_at: datetime


class PDFListResponse(BaseModel):
    """Response for GET /project/pdfs."""

    pdfs: List[PDFMetadata]
    count: int


class PDFPageInfo(BaseModel):
    """Information about a PDF page."""

    page_num: int
    width: float
    height: float
    has_text_layer: bool


class PDFPagesResponse(BaseModel):
    """Response for GET /pdf/{doc_id}/pages."""

    doc_id: str
    doc_name: str
    pages: List[PDFPageInfo]
    page_count: int


class PDFRenderRequest(BaseModel):
    """Request for PDF rendering."""

    format: str = "png"  # "png" or "svg"
    dpi: int = 150


# ========== Block Schemas ==========

class BlockData(BaseModel):
    """Data for a single block."""

    id: str
    document_id: str
    section: Optional[str]
    content: str
    block_type: str  # "chapter", "section", "paragraph"
    pages: List[int]
    bboxes: List[List[float]]  # List of (x, y, w, h) tuples
    page_rotations: List[int] = Field(default_factory=list, description="Rotation per page in degrees")
    ai_generated: bool
    created_at: datetime
    modified_at: datetime


class BlocksListResponse(BaseModel):
    """Response for GET /blocks/{doc_id}."""

    doc_id: str
    blocks: List[BlockData]
    count: int


class BlockDetailResponse(BaseModel):
    """Response for GET /block/{id}."""

    block: BlockData


class BlockCreateRequest(BaseModel):
    """Request for POST /block."""

    document_id: str
    section: Optional[str] = None
    content: str = Field(..., description="Block content")
    block_type: str = "paragraph"
    pages: List[int] = Field(..., description="Page numbers")
    bboxes: List[List[float]] = Field(..., description="Bounding boxes")
    page_rotations: List[int] = Field(default_factory=list, description="Rotation per page in degrees")
    ai_generated: bool = False


class BlockCreateResponse(BaseModel):
    """Response for POST /block."""

    block: BlockData
    message: str


class BlockUpdateRequest(BaseModel):
    """Request for PATCH /block/{id}."""

    section: Optional[str] = None
    content: Optional[str] = None
    block_type: Optional[str] = None
    ai_generated: Optional[bool] = None


class BlockUpdateResponse(BaseModel):
    """Response for PATCH /block/{id}."""

    block: BlockData
    message: str


class BlockDeleteResponse(BaseModel):
    """Response for DELETE /block/{id}."""

    message: str
    deleted_id: str


# ========== Segmentation Schemas ==========

class SegmentationRequest(BaseModel):
    """Request for POST /pdf/{doc_id}/parse."""

    overwrite_existing: bool = False


class SegmentationResponse(BaseModel):
    """Response for POST /pdf/{doc_id}/parse."""

    doc_id: str
    blocks_created: int
    message: str


# ========== Error Response ==========

class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    status_code: int
