from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from normen_tool.api.routers.project import router as project_router
from normen_tool.api.routers.pdf import router as pdf_router
from normen_tool.api.routers.block import router as block_router
from normen_tool.api.routers.export import router as export_router
from normen_tool.api.routers.frontend import router as frontend_router

app = FastAPI(title="Normen Segmentierungs Tool")
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(frontend_router)
app.include_router(project_router)
app.include_router(pdf_router)
app.include_router(block_router)
app.include_router(export_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
