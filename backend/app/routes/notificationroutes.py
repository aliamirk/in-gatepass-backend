from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from ..database import get_db
from ..services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Default system user ID (no authentication required)
SYSTEM_USER_ID = "system"


def serialize_notification(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    result = doc.copy()
    # Convert ObjectId to string if present
    if "_id" in result:
        result["_id"] = str(result["_id"]) if isinstance(result["_id"], ObjectId) else result["_id"]
    # Ensure all fields are JSON-serializable
    if "gatepass_id" in result and isinstance(result["gatepass_id"], ObjectId):
        result["gatepass_id"] = str(result["gatepass_id"])
    return result


@router.get("/admin")
async def notifications_for_admin(db=Depends(get_db)):
    """
    Get all notifications for admin.
    Returns notifications for user_id='admin'.
    """
    notifications = notification_service.get_notifications_for_user(db, "admin")
    return [serialize_notification(notif) for notif in notifications]


@router.get("/hr")
async def notifications_for_hr(db=Depends(get_db)):
    """
    Get all notifications for HR.
    Returns notifications for user_id='hr'.
    """
    notifications = notification_service.get_notifications_for_user(db, "hr")
    return [serialize_notification(notif) for notif in notifications]


@router.get("/mark-read/{notification_id}")
async def mark_notification_read(notification_id: str, db=Depends(get_db)):
    """
    Mark a notification as read.
    """
    result = db["notifications"].update_one(
        {"notf_id": notification_id},
        {"$set": {"is_read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success", "message": "Notification marked as read"}
