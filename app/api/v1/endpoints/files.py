from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter
import os
from app.core.config import BASE_DIR


router = APIRouter()


@router.get("/{filename}/")
async def get_image(filename: str):
    file_path = os.path.join(BASE_DIR, filename)
    return FileResponse(file_path, media_type="image/jpeg")
