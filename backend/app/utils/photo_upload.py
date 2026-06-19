import os
from uuid import uuid4
from fastapi import UploadFile

from ..config import settings


def ensure_photo_dir() -> str:
    base = settings.MEDIA_ROOT
    photo_dir = os.path.join(base, settings.PHOTO_DIR)
    os.makedirs(photo_dir, exist_ok=True)
    return photo_dir


async def save_photo_file(file: UploadFile) -> str:
    photo_dir = ensure_photo_dir()
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(photo_dir, filename)

    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    return filename
