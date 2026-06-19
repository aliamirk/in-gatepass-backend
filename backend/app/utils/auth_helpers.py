from typing import List

from fastapi import Depends, HTTPException, Header, status
from passlib.context import CryptContext

from ..database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def get_current_user(
    db=Depends(get_db),
    username: str = Header(..., alias="X-Username"),
    password: str = Header(..., alias="X-Password"),
):
    """
    Simple auth:
    Frontend must send headers:
    X-Username: hr | admin | gate
    X-Password: 12345
    """

    user = db["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User disabled")

    return user


def require_roles(roles: List[str]):
    async def dependency(current_user=Depends(get_current_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user

    return dependency
