from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
import pytz

from fastapi import HTTPException
from bson import ObjectId

from ..utils.generate_qr import generate_qr_for_pass
from ..schemas.gatepass import GatePassCreate, GatePassFilter


# Pakistan timezone
PKT = pytz.timezone('Asia/Karachi')


# -----------------------------
# Helpers
# -----------------------------

def _get_pk_time():
    """Get current time in Pakistan timezone."""
    return datetime.now(PKT)


def _normalize_id(doc: Dict[str, Any]):
    """Ensure _id is always a string for API responses."""
    if isinstance(doc.get("_id"), ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc


def _new_gatepass_number(db):
    year = _get_pk_time().year
    count = db["gatepasses"].count_documents({"year": year}) + 1
    return f"GP-{year}-{count:04d}"


def _find_gatepass(db, query: Dict[str, Any]):
    """Unified fetch function supporting both string and ObjectId."""
    doc = db["gatepasses"].find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Gate pass not found")
    return _normalize_id(doc)


def _append_status_history(doc: Dict[str, Any], new_status: str, user_id: str):
    doc.setdefault("status_history", []).append({
        "status": new_status,
        "changed_at": _get_pk_time(),
        "changed_by": user_id,
    })


def _update_doc(db, doc: Dict[str, Any]):
    """Safely update doc using correct filter."""
    raw_id = doc["_id"]
    filter_id = ObjectId(raw_id) if ObjectId.is_valid(raw_id) else raw_id

    update_data = {k: v for k, v in doc.items() if k != "_id"}
    db["gatepasses"].update_one({"_id": filter_id}, {"$set": update_data})
    return doc


# -----------------------------
# CRUD functions
# -----------------------------

def create_gatepass(db, hr_user_id: str, payload: GatePassCreate) -> Dict[str, Any]:
    number = _new_gatepass_number(db)
    now = _get_pk_time()

    doc = {
        "_id": uuid4().hex,
        "number": number,
        "person_name": payload.person_name,
        "description": payload.description,
        "created_by": hr_user_id,
        "status": "created",
        "created_at": now,
        "entry_time": None,
        "qr_code_url": generate_qr_for_pass(number),
        "year": now.year,
    }

    db["gatepasses"].insert_one(doc)
    return doc


def get_gatepass_by_id(db, pass_id: str):
    query = {"_id": pass_id}

    if ObjectId.is_valid(pass_id):
        doc = db["gatepasses"].find_one({"_id": ObjectId(pass_id)}) or db["gatepasses"].find_one(query)
    else:
        doc = db["gatepasses"].find_one(query)

    if not doc:
        raise HTTPException(status_code=404, detail="Gate pass not found")

    return _normalize_id(doc)


def get_gatepass_by_number(db, number: str):
    return _find_gatepass(db, {"number": number})


def list_gatepasses(db, filter_obj: Optional[GatePassFilter] = None):
    query = {}

    if filter_obj:
        if filter_obj.status:
            query["status"] = filter_obj.status
        if filter_obj.created_by:
            query["created_by"] = filter_obj.created_by

    docs = list(db["gatepasses"].find(query).sort("created_at", -1).limit(200))
    return [_normalize_id(doc) for doc in docs]


def update_gatepass_on_entry(db, pass_number: str, gate_user_id: str) -> Dict[str, Any]:
    """Set status to 'entered' and record entry_time on first call; idempotent thereafter."""
    doc = get_gatepass_by_number(db, pass_number)   # raises 404 if missing

    doc["status"] = "entered"
    if not doc.get("entry_time"):                    # preserve original entry_time on repeat scans
        doc["entry_time"] = _get_pk_time()

    return _update_doc(db, doc)



