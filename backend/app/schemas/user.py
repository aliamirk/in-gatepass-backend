from pydantic import BaseModel
from ..models.user import UserRole


class UserBase(BaseModel):
    name: str
    username: str
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(UserBase):
    id: str
    is_active: bool = True

    class Config:
        from_attributes = True
