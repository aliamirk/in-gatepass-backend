from typing import List, Dict, Any

from ..schemas.gatepass import GatePassFilter
from . import gatepass_service, notification_service


def get_pending_gatepasses(db) -> List[Dict[str, Any]]:
    filter_obj = GatePassFilter(status="pending")
    return gatepass_service.list_gatepasses(db, filter_obj)


def approve_gatepass(db, pass_id: str, admin_user_id: str) -> Dict[str, Any]:
    doc = gatepass_service.approve_gatepass(db, pass_id, admin_user_id)
    # Notify HR that gatepass has been approved
    notification_service.create_notification(
        db=db,
        user_id="hr",  # HR user identifier
        title="Gate pass approved",
        message=f"Gate pass {doc['number']} has been approved",
        gatepass_id=doc["_id"],
    )
    return doc


def reject_gatepass(db, pass_id: str, admin_user_id: str) -> Dict[str, Any]:
    doc = gatepass_service.reject_gatepass(db, pass_id, admin_user_id)
    # Notify HR that gatepass has been rejected
    notification_service.create_notification(
        db=db,
        user_id="hr",  # HR user identifier
        title="Gate pass rejected",
        message=f"Gate pass {doc['number']} has been rejected",
        gatepass_id=doc["_id"],
    )
    return doc

def delete_gatepass(db, pass_id: str, admin_user_id: str) -> Dict[str, Any]:
    doc = gatepass_service.delete_gatepass(db, pass_id, admin_user_id)
    # Notify HR that gatepass has been deleted
    notification_service.create_notification(
        db=db,
        user_id="hr",  # HR user identifier
        title="Gate pass deleted",
        message=f"Gate pass {doc['number']} has been deleted",
        gatepass_id=doc["_id"],
    )
    return doc

def list_all_gatepasses(db, status: str | None) -> List[Dict[str, Any]]:
    filter_obj = GatePassFilter(status=status)
    return gatepass_service.list_gatepasses(db, filter_obj)

