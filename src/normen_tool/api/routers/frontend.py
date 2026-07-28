from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

@router.get("/")
def get_frontend_index():
    file_path = Path(__file__).resolve().parents[2] / "static" / "index.html"
    return FileResponse(path=file_path, media_type="text/html")
