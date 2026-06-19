from typing import List, Dict, Any
from ..schemas.gatepass import GatePassCreate, GatePassFilter
from . import gatepass_service


def create_gatepass_for_hr(db, hr_user_id: str, payload: GatePassCreate) -> Dict[str, Any]:
    return gatepass_service.create_gatepass(db, hr_user_id, payload)


def list_hr_gatepasses(db, hr_user_id: str, status: str | None) -> List[Dict[str, Any]]:
    filter_obj = GatePassFilter(status=status, created_by=hr_user_id)
    return gatepass_service.list_gatepasses(db, filter_obj)


def get_hr_gatepass_detail(db, pass_id: str) -> Dict[str, Any]:
    return gatepass_service.get_gatepass_by_number(db, pass_id)
