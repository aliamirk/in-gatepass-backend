from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel


class GatePassCreate(BaseModel):
    person_name: str
    description: str


class GatePassOut(BaseModel):
    id: str
    number: str
    person_name: str
    description: str
    created_by: str
    status: Literal["created", "entered"]
    created_at: datetime
    entry_time: Optional[datetime] = None
    qr_code_url: Optional[str] = None

    class Config:
        from_attributes = True


class GatePassFilter(BaseModel):
    status: Optional[str] = None
    created_by: Optional[str] = None


class GatePassScanEntry(BaseModel):
    pass_number: str


class PhotoInfo(BaseModel):
    photo_id: str
    gatepass_id: str
    file_url: str
    type: str  # "exit" or "return"
    captured_at: datetime
    captured_by: str
    pass_number: Optional[str] = None
