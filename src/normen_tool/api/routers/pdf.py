from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import FileResponse
from typing import Optional, List

from normen_tool.api.dependencies import get_project_context
from normen_tool.api.schemas import (
    PDFPagesResponse,
    PDFPageInfo,
    SegmentationRequest,
    SegmentationResponse,
)
from normen_tool.pdf_handler import PDFHandler
from normen_tool.segmentation import segment_pdf_blocks

router = APIRouter(tags=["pdf"])


@router.get("/pdf/{doc_id}/pages", response_model=PDFPagesResponse)
def get_pdf_pages(doc_id: str, context=Depends(get_project_context)):
    document = context.db_client.get_document(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    with PDFHandler(document.path) as handler:
        pages = [
            PDFPageInfo(
                page_num=i + 1,
                width=page_info["width"],
                height=page_info["height"],
                has_text_layer=document.has_text_layer,
            )
            for i in range(handler.page_count)
            for page_info in [handler.get_page_metadata(i)]
        ]

    return {
        "doc_id": document.id,
        "doc_name": document.name,
        "pages": pages,
        "page_count": document.page_count,
    }


@router.get("/pdf/{doc_id}/rendered/{page_num}")
def render_pdf_page(
    doc_id: str,
    page_num: int,
    format: str = Query("png", pattern="^(png|svg)$"),
    dpi: int = Query(150, ge=50, le=600),
    context=Depends(get_project_context),
):
    document = context.db_client.get_document(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    if format != "png":
        raise HTTPException(status_code=501, detail="Only PNG rendering is supported at this time.")

    with PDFHandler(document.path) as handler:
        if page_num < 1 or page_num > handler.page_count:
            raise HTTPException(status_code=404, detail="Page not found.")
        image_bytes = handler.get_page_image(page_num - 1, zoom=dpi / 72.0)

    return Response(content=image_bytes, media_type="image/png")


@router.get("/pdf/{doc_id}/download")
def download_pdf_document(doc_id: str, context=Depends(get_project_context)):
    document = context.db_client.get_document(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return FileResponse(path=document.path, filename=document.name, media_type="application/pdf")


@router.post("/pdf/{doc_id}/parse", response_model=SegmentationResponse)
def parse_pdf_document(
    doc_id: str,
    request: SegmentationRequest,
    context=Depends(get_project_context),
):
    document = context.db_client.get_document(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    with PDFHandler(document.path) as handler:
        all_blocks = []
        for page_num in range(handler.page_count):
            page_blocks = handler.extract_text_and_bboxes(page_num)
            all_blocks.extend(
                (block["text"], tuple(block["bbox"]), page_num)
                for block in page_blocks
                if block["block_type"] == "text"
            )

    segmented_blocks = segment_pdf_blocks(all_blocks)

    if request.overwrite_existing:
        context.db_client.delete_blocks_for_document(doc_id)

    block_records = []
    for segment in segmented_blocks:
        pages = [segment.page_start] if segment.page_start == segment.page_end else [segment.page_start, segment.page_end]
        bboxes = [
            list(segment.bbox_start) if segment.bbox_start else [],
        ]
        if segment.bbox_end and segment.page_end != segment.page_start:
            bboxes.append(list(segment.bbox_end))

        block_records.append(
            {
                "content": segment.content,
                "section": segment.section,
                "block_type": segment.segment_type,
                "pages": pages,
                "bboxes": bboxes,
                "ai_generated": False,
            }
        )

    context.db_client.bulk_insert_blocks(doc_id, block_records)

    return {
        "doc_id": doc_id,
        "blocks_created": len(block_records),
        "message": f"Parsed {len(block_records)} blocks from document.",
    }
