from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from ..config import settings

router = APIRouter(prefix="/qr", tags=["qr"])

@router.get("/{pass_number}")
async def get_qr(pass_number: str):
    """
    Returns QR image for the given gatepass number.
    """
    qr_path = os.path.join(settings.MEDIA_ROOT, settings.QR_DIR, f"{pass_number}.png")
    if not os.path.exists(qr_path):
        raise HTTPException(status_code=404, detail="QR not found")
    return FileResponse(qr_path, media_type="image/png", filename=f"{pass_number}.png")
