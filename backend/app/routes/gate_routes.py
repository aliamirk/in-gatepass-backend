from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from ..database import get_db
from ..services import gate_service, gatepass_service
from ..schemas.gatepass import GatePassOut

router = APIRouter(prefix="/gate", tags=["gate"])

# Default system user ID (no authentication required)
SYSTEM_USER_ID = "system"


def serialize_gatepass(doc) -> GatePassOut:
    from bson import ObjectId
    doc_id = str(doc["_id"]) if isinstance(doc["_id"], ObjectId) else doc["_id"]
    created_by = str(doc["created_by"]) if isinstance(doc["created_by"], ObjectId) else doc["created_by"]
    
    return GatePassOut(
        id=doc_id,
        number=doc["number"],
        person_name=doc["person_name"],
        description=doc["description"],
        created_by=created_by,
        status=doc["status"],
        created_at=doc["created_at"],
        entry_time=doc.get("entry_time"),
        qr_code_url=doc.get("qr_code_url"),
    )


@router.post("/scan-entry", response_model=GatePassOut)
async def scan_entry(
    pass_number: str = Form(...),
    files: List[UploadFile] = File(...),
    db=Depends(get_db),
):
    """
    Scan QR code at gate entry.
    - Requires pass_number and one or more photo files
    - Saves all photos atomically
    - Updates gatepass status to 'entered'
    """
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required")
    doc = await gate_service.process_entry_scan(db, pass_number, files, SYSTEM_USER_ID)
    return serialize_gatepass(doc)



@router.get("/gatepass/number/{pass_number}", response_model=GatePassOut)
async def get_gatepass_by_number(pass_number: str, db=Depends(get_db)):
    """
    Get gatepass details by pass number (e.g., GP-2024-0001).
    Use this endpoint when scanning QR code which contains the pass number.
    """
    doc = gatepass_service.get_gatepass_by_number(db, pass_number)
    return serialize_gatepass(doc)


@router.get("/gatepass/id/{pass_number}", response_model=GatePassOut)
async def get_gatepass_by_number(pass_number: str, db=Depends(get_db)):
    """
    Get gatepass details by pass ID.
    Use this endpoint when you have the gatepass ID.
    """
    doc = gatepass_service.get_gatepass_by_number(db, pass_number)
    return serialize_gatepass(doc)


@router.get("/photos/{pass_number}")
async def get_gatepass_photos(pass_number: str, db=Depends(get_db)):
    """
    Get all photos associated with a gatepass by pass number.
    Returns exit and return photos with their details.
    """
    from bson import ObjectId
    
    # Query photos by pass_number (since we store pass_number in photo records)
    photos = list(db["photos"].find({"pass_number": pass_number, "type": "entry"}).sort("captured_at", 1))
    
    # Convert ObjectId to string for JSON serialization
    result = []
    for photo in photos:
        photo_dict = {
            "photo_id": photo.get("photo_id"),
            "gatepass_id": str(photo.get("gatepass_id")) if isinstance(photo.get("gatepass_id"), ObjectId) else photo.get("gatepass_id"),
            "file_url": photo.get("file_url"),
            "type": photo.get("type"),
            "captured_at": photo.get("captured_at"),
            "captured_by": photo.get("captured_by"),
            "pass_number": photo.get("pass_number"),
        }
        if "_id" in photo:
            photo_dict["_id"] = str(photo["_id"]) if isinstance(photo["_id"], ObjectId) else photo["_id"]
        result.append(photo_dict)
    
    return {"pass_number": pass_number, "photos": result, "total": len(result)}
