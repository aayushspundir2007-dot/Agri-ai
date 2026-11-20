"""Authentication router — /api/auth/login, /api/auth/logout, /api/auth/me."""
import json
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.security import create_token, verify_password
from app.models.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

def _load_users() -> dict:
    if settings.USERS_FILE.exists():
        return json.loads(settings.USERS_FILE.read_text())
    return {}

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    users = _load_users()
    record = users.get(body.username)
    if not record or not verify_password(body.password, record["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_token({"sub": body.username, "role": record["role"]})
    return TokenResponse(
        access_token=token,
        username=body.username,
        name=record["name"],
        role=record["role"],
    )

@router.post("/logout")
def logout():
    # Stateless JWT — client discards token
    return {"detail": "Logged out successfully"}

@router.get("/me")
def me_endpoint(credentials: str = None):
    return {"detail": "Use Authorization: Bearer <token>"}
