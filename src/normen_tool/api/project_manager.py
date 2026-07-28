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


def _collapse_duplicate_segments(path: Path) -> Path:
    parts = list(path.parts)
    if not parts:
        return path

    collapsed = [parts[0]]
    for segment in parts[1:]:
        if segment != collapsed[-1]:
            collapsed.append(segment)

    return Path(*collapsed)


def _resolve_project_path(project_dir: str) -> Path:
    normalized_input = project_dir.strip().strip('"').strip("'")
    raw_path = Path(normalized_input).expanduser()
    resolved_path = raw_path.resolve()

    if resolved_path.exists() and resolved_path.is_dir():
        return resolved_path

    fallback_raw = _collapse_duplicate_segments(raw_path)
    if fallback_raw != raw_path:
        fallback_resolved = fallback_raw.resolve()
        if fallback_resolved.exists() and fallback_resolved.is_dir():
            logger.warning(
                "Project path corrected from %s to %s due to duplicate directory segments.",
                resolved_path,
                fallback_resolved,
            )
            return fallback_resolved

    # Handle relative paths where duplicates only appear after cwd resolution.
    resolved_fallback = _collapse_duplicate_segments(resolved_path)
    if (
        resolved_fallback != resolved_path
        and resolved_fallback.exists()
        and resolved_fallback.is_dir()
    ):
        logger.warning(
            "Project path corrected from %s to %s due to duplicate directory segments after resolution.",
            resolved_path,
            resolved_fallback,
        )
        return resolved_fallback

    return resolved_path


def open_project(app: FastAPI, project_dir: str) -> ProjectContext:
    project_path = _resolve_project_path(project_dir)
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
