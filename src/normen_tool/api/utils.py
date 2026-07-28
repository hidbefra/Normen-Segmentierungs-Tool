from typing import List

from normen_tool.api.schemas import BlockData, PDFMetadata
from normen_tool.db.models import Block, Document


def document_to_pdf_metadata(document: Document) -> PDFMetadata:
    return PDFMetadata(
        id=document.id,
        name=document.name,
        path=document.path,
        page_count=document.page_count,
        has_text_layer=document.has_text_layer,
        created_at=document.created_at,
        modified_at=document.modified_at,
    )


def block_to_block_data(block: Block) -> BlockData:
    return BlockData(
        id=block.id,
        document_id=block.document_id,
        section=block.section,
        content=block.content,
        block_type=block.block_type,
        pages=list(block.pages or []),
        bboxes=[list(item) for item in (block.bboxes or [])],
        ai_generated=block.ai_generated,
        created_at=block.created_at,
        modified_at=block.modified_at,
    )
