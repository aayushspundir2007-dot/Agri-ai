"""Pydantic request/response schemas for all API endpoints."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Auth ─────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    username:     str
    name:         str
    role:         str

class TokenData(BaseModel):
    username: Optional[str] = None
    role:     Optional[str] = None


# ── Users ────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    name:     str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6)
    role:     str = Field("viewer", pattern="^(admin|viewer)$")

class UserResponse(BaseModel):
    username: str
    name:     str
    role:     str


# ── Crop Recommendation ──────────────────────────────────────────
class CropRequest(BaseModel):
    N:           float = Field(..., ge=0,   le=200,  description="Nitrogen")
    P:           float = Field(..., ge=0,   le=200,  description="Phosphorus")
    K:           float = Field(..., ge=0,   le=250,  description="Potassium")
    temperature: float = Field(..., ge=-5,  le=55,   description="Temperature °C")
    humidity:    float = Field(..., ge=0,   le=100,  description="Humidity %")
    ph:          float = Field(..., ge=0,   le=14,   description="Soil pH")
    rainfall:    float = Field(..., ge=0,   le=5000, description="Rainfall mm")

class CropResponse(BaseModel):
    crop:          str
    probabilities: Dict[str, float]
    model:         str = "RandomForest"


# ── Yield Prediction ─────────────────────────────────────────────
class YieldRequest(BaseModel):
    area:        str   = Field(..., min_length=1, description="Country / Area")
    item:        str   = Field(..., min_length=1, description="Crop name")
    year:        int   = Field(..., ge=1961, le=2100)
    rainfall:    float = Field(..., ge=0,    le=10000, description="mm/year")
    pesticides:  float = Field(..., ge=0,              description="tonnes")
    temperature: float = Field(..., ge=-10,  le=60,    description="°C")

class YieldResponse(BaseModel):
    yield_hgha: float
    area:       str
    item:       str
    year:       int
    model:      str = "ExtraTrees"


# ── Disease Detection ─────────────────────────────────────────────
class DiseaseResponse(BaseModel):
    predicted_class: str
    confidence:      float
    top5:            Dict[str, float]
    model:           str = "HistGradientBoosting"


# ── Health ───────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status:        str
    models_loaded: Dict[str, bool]
    uptime_seconds:float
    version:       str = "2.0.0"
