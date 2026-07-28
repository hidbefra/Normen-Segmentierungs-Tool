from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

router = APIRouter()

router.mount("/static", StaticFiles(directory="src/normen_tool/static"), name="static")
