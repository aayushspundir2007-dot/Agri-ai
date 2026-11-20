"""Application settings — loaded from environment variables or .env file."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]

class Settings:
    JWT_SECRET:       str  = os.getenv("JWT_SECRET", "agrismart-dev-secret-change-in-prod")
    JWT_ALGORITHM:    str  = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_HOURS: int  = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
    API_HOST:         str  = os.getenv("API_HOST", "0.0.0.0")
    API_PORT:         int  = int(os.getenv("API_PORT", "8000"))
    STREAMLIT_API_URL:str  = os.getenv("STREAMLIT_API_URL", "http://localhost:8000")
    USERS_FILE:       Path = ROOT / os.getenv("USERS_FILE", "users.json")
    LOG_FILE:         Path = ROOT / os.getenv("LOG_FILE", "predictions.log")
    MODELS_DIR:       Path = ROOT / "models"
    REPORTS_DIR:      Path = ROOT / "reports"
    SRC_DIR:          Path = ROOT / "src"

settings = Settings()
