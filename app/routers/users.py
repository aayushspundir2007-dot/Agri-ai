"""User management router — /api/users (admin only)."""
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.security import hash_password
from app.models.auth import require_admin
from app.models.schemas import UserCreate, UserResponse, TokenData

router = APIRouter(prefix="/api/users", tags=["users"])

def _load() -> dict:
    return json.loads(settings.USERS_FILE.read_text()) if settings.USERS_FILE.exists() else {}

def _save(users: dict):
    settings.USERS_FILE.write_text(json.dumps(users, indent=2))


@router.get("", response_model=List[UserResponse])
def list_users(_: TokenData = Depends(require_admin)):
    users = _load()
    return [UserResponse(username=k, name=v["name"], role=v["role"])
            for k, v in users.items()]


@router.post("", response_model=UserResponse, status_code=201)
def create_user(body: UserCreate, _: TokenData = Depends(require_admin)):
    users = _load()
    if body.username in users:
        raise HTTPException(status_code=409, detail=f"User '{body.username}' already exists")
    users[body.username] = {
        "password": hash_password(body.password),
        "role":     body.role,
        "name":     body.name,
    }
    _save(users)
    return UserResponse(username=body.username, name=body.name, role=body.role)


@router.delete("/{username}", status_code=204)
def delete_user(username: str, current: TokenData = Depends(require_admin)):
    if username == current.username:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    users = _load()
    if username not in users:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    del users[username]
    _save(users)
