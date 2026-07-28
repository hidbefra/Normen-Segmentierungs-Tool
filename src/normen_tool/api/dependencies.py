from fastapi import Request, HTTPException

from normen_tool.api.project_manager import get_project_context as _get_project_context
from normen_tool.api.project_manager import ProjectContext


def get_project_context(request: Request) -> ProjectContext:
    context = _get_project_context(request.app)
    if context.db_client is None:
        raise HTTPException(
            status_code=400,
            detail="Project is not open. Call /project/open first.",
        )
    return context
