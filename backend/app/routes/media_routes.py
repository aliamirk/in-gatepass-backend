from datetime import datetime
import os
import pytz

from fastapi import APIRouter, UploadFile, Depends, HTTPException
from fastapi.responses import FileResponse

from ..database import get_db
from ..utils.photo_upload import save_photo_file
from ..config import settings

router = APIRouter(prefix="/media", tags=["media"])


# Pakistan timezone
PKT = pytz.timezone('Asia/Karachi')


def _get_pk_time():
    """Get current time in Pakistan timezone."""
    return datetime.now(PKT)


@router.post("/upload-photo")
async def upload_photo(file: UploadFile, db=Depends(get_db)):
    from bson import ObjectId
    filename = await save_photo_file(file)
    record = {
        "photo_id": filename,
        "gatepass_id": None,
        "file_url": f"/media/photo/{filename}",
        "type": "generic",
        "captured_at": _get_pk_time(),
        "captured_by": None,
    }
    db["photos"].insert_one(record)
    # Convert ObjectId to string for JSON serialization
    if "_id" in record and isinstance(record["_id"], ObjectId):
        record["_id"] = str(record["_id"])
    return record


@router.get("/photo/{photo_id}")
async def get_photo(photo_id: str):
    path = os.path.join(settings.MEDIA_ROOT, settings.PHOTO_DIR, photo_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(path)