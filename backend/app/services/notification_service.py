from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any
import pytz


# Pakistan timezone
PKT = pytz.timezone('Asia/Karachi')


def _get_pk_time():
    """Get current time in Pakistan timezone."""
    return datetime.now(PKT)


def create_notification(db, user_id: str, title: str, message: str, gatepass_id: str) -> Dict[str, Any]:
    from bson import ObjectId
    doc = {
        "notf_id": uuid4().hex,
        "user_id": user_id,
        "title": title,
        "message": message,
        "gatepass_id": gatepass_id,
        "is_read": False,
        "created_at": _get_pk_time(),
    }
    db["notifications"].insert_one(doc)
    # MongoDB adds _id field, convert to string if it's ObjectId
    # Note: insert_one may modify doc to add _id
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc


def get_notifications_for_user(db, user_id: str) -> List[Dict[str, Any]]:
    from bson import ObjectId
    docs = list(db["notifications"].find({"user_id": user_id}).sort("created_at", -1))
    # Convert all ObjectId _id fields to strings
    for doc in docs:
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        # Also convert gatepass_id if it's ObjectId
        if "gatepass_id" in doc and isinstance(doc["gatepass_id"], ObjectId):
            doc["gatepass_id"] = str(doc["gatepass_id"])
    return docs