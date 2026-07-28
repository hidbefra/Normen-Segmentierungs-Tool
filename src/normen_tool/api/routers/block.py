from fastapi import APIRouter, Depends, HTTPException

from normen_tool.api.dependencies import get_project_context
from normen_tool.api.schemas import (
    BlockCreateRequest,
    BlockCreateResponse,
    BlockUpdateRequest,
    BlockUpdateResponse,
    BlockDeleteResponse,
    BlocksListResponse,
    BlockDetailResponse,
)
from normen_tool.api.utils import block_to_block_data

router = APIRouter(tags=["blocks"])


@router.get("/blocks/{doc_id}", response_model=BlocksListResponse)
def list_blocks(doc_id: str, context=Depends(get_project_context)):
    document = context.db_client.get_document(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    blocks = context.db_client.list_blocks(doc_id)
    return {
        "doc_id": doc_id,
        "blocks": [block_to_block_data(b) for b in blocks],
        "count": len(blocks),
    }


@router.get("/block/{block_id}", response_model=BlockDetailResponse)
def get_block(block_id: str, context=Depends(get_project_context)):
    block = context.db_client.get_block(block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found.")

    return {"block": block_to_block_data(block)}


@router.post("/block", response_model=BlockCreateResponse)
def create_block(request: BlockCreateRequest, context=Depends(get_project_context)):
    document = context.db_client.get_document(request.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    block = context.db_client.add_block(
        document_id=request.document_id,
        content=request.content,
        section=request.section or "",
        block_type=request.block_type,
        pages=request.pages,
        bboxes=[tuple(item) for item in request.bboxes],
        ai_generated=request.ai_generated,
    )
    return {"block": block_to_block_data(block), "message": "Block created successfully."}


@router.patch("/block/{block_id}", response_model=BlockUpdateResponse)
def update_block(block_id: str, request: BlockUpdateRequest, context=Depends(get_project_context)):
    block = context.db_client.get_block(block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found.")

    updates = {
        key: value
        for key, value in request.model_dump(exclude_unset=True).items()
        if value is not None
    }

    updated = context.db_client.update_block(block_id, **updates)
    if updated is None:
        raise HTTPException(status_code=500, detail="Failed to update block.")

    return {"block": block_to_block_data(updated), "message": "Block updated successfully."}


@router.delete("/block/{block_id}", response_model=BlockDeleteResponse)
def delete_block(block_id: str, context=Depends(get_project_context)):
    deleted = context.db_client.delete_block(block_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Block not found.")

    return {"deleted_id": block_id, "message": "Block deleted successfully."}
