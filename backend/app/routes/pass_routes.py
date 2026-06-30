from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..database import get_db
from ..schemas.gatepass import GatePassOut, GatePassFilter
from ..services import gatepass_service

router = APIRouter(prefix="/pass", tags=["gatepass"])


def serialize_gatepass(doc) -> GatePassOut:
    # Convert ObjectId to string for JSON serialization
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


@router.get("/list", response_model=List[GatePassOut])
async def list_passes(
    status: str | None = None,
    db=Depends(get_db),
):
    filter_obj = GatePassFilter(status=status)
    docs = gatepass_service.list_gatepasses(db, filter_obj)
    return [serialize_gatepass(d) for d in docs]


@router.delete("/{pass_id}")
async def delete_gatepass(pass_id: str, db=Depends(get_db)):
    """Delete a gatepass by its ID."""
    deleted = gatepass_service.delete_gatepass(db, pass_id)
    return {"message": f"Gate pass {deleted['number']} deleted successfully", "id": pass_id}
