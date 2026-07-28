import csv
import json
from pathlib import Path
from typing import Iterable

from normen_tool.db.client import DBClient
from normen_tool.db.models import Block, Document


CSV_COLUMNS = [
    "ID",
    "doc_name",
    "section",
    "content",
    "DeepLink_Editor",
    "block_type",
    "pages",
    "bboxes",
    "ai_generated",
]


def _make_deep_link(base_url: str, document_id: str, block_id: str) -> str:
    return f"{base_url}?doc={document_id}&block={block_id}"


def _serialize_pages(pages: Iterable[int]) -> str:
    return json.dumps(list(pages), ensure_ascii=False)


def _serialize_bboxes(bboxes: Iterable[Iterable[float]]) -> str:
    return json.dumps([list(item) for item in bboxes], ensure_ascii=False)


def _iter_export_rows(db_client: DBClient, deep_link_base: str) -> Iterable[dict]:
    for document in db_client.list_documents():
        blocks = db_client.list_blocks(document.id)
        for block in blocks:
            yield {
                "ID": block.id,
                "doc_name": document.name,
                "section": block.section or "",
                "content": block.content,
                "DeepLink_Editor": _make_deep_link(deep_link_base, document.id, block.id),
                "block_type": block.block_type,
                "pages": _serialize_pages(block.pages or []),
                "bboxes": _serialize_bboxes(block.bboxes or []),
                "ai_generated": str(block.ai_generated),
            }


def export_to_csv(project_dir: Path, db_client: DBClient, deep_link_base: str = "http://localhost:8000/ui") -> Path:
    project_path = Path(project_dir)
    if not project_path.exists() or not project_path.is_dir():
        raise FileNotFoundError(f"Project directory does not exist: {project_path}")

    csv_path = project_path / "norm_data_powerquery.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in _iter_export_rows(db_client, deep_link_base):
            writer.writerow(row)

    return csv_path
