from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from normen_tool.api.dependencies import get_project_context
from normen_tool.api.schemas import PDFRenderRequest
from normen_tool.export import export_to_csv

router = APIRouter(tags=["export"])


@router.get("/export/csv")
def get_export_csv(context=Depends(get_project_context)):
    project_dir = context.project_dir
    if project_dir is None:
        raise HTTPException(status_code=400, detail="Project is not open.")

    try:
        csv_path = export_to_csv(project_dir, context.db_client)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return FileResponse(path=csv_path, filename=csv_path.name, media_type="text/csv")
