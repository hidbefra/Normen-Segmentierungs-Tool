import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from normen_tool.db.client import DBClient
from normen_tool.pdf_handler import PDFHandler

logger = logging.getLogger(__name__)


class ProjectContext:
    def __init__(self) -> None:
        self.project_dir: Optional[Path] = None
        self.db_file: Optional[Path] = None
        self.db_client: Optional[DBClient] = None
        self.created: bool = False


def get_project_context(app: FastAPI) -> ProjectContext:
    context = getattr(app.state, "project_context", None)
    if context is None:
        context = ProjectContext()
        app.state.project_context = context
    return context


def open_project(app: FastAPI, project_dir: str) -> ProjectContext:
    project_path = Path(project_dir).expanduser().resolve()
    if not project_path.exists() or not project_path.is_dir():
        raise ValueError(f"Project directory does not exist: {project_path}")

    db_file = project_path / "project_database.db"
    created = not db_file.exists()

    client = DBClient(str(db_file))
    client.init_db()
    _sync_documents_with_project_folder(client, project_path)

    context = get_project_context(app)
    context.project_dir = project_path
    context.db_file = db_file
    context.db_client = client
    context.created = created
    logger.info("Project opened: %s", project_path)
    return context


def _sync_documents_with_project_folder(client: DBClient, project_path: Path) -> None:
    pdf_files = sorted(project_path.glob("*.pdf"))
    for pdf_path in pdf_files:
        if client.get_document_by_name(pdf_path.name) is not None:
            continue

        with PDFHandler(pdf_path) as handler:
            client.add_document(
                name=pdf_path.name,
                path=str(pdf_path),
                page_count=handler.page_count,
                has_text_layer=handler.has_text_layer(),
                doc_metadata=handler.get_document_metadata(),
            )
