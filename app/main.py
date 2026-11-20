"""AgriSmart AI — FastAPI backend (v2.0)"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.ml_loader import ml
from app.core.monitoring import monitor
from app.models.schemas import HealthResponse
from app.routers import auth, predict, users

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup — load all models once
    ml.load_all()
    yield
    # shutdown — nothing to clean up


app = FastAPI(
    title="AgriSmart AI API",
    description="Production-grade ML backend for crop recommendation, yield prediction and plant disease detection.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(users.router)


# ── Health ────────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(
        status="ok",
        models_loaded=ml.models_loaded(),
        uptime_seconds=round(time.time() - START_TIME, 1),
    )


# ── Analytics ─────────────────────────────────────────────────────
@app.get("/api/analytics", tags=["system"])
def analytics():
    return monitor.analytics()


# ── Metrics (reports JSON) ────────────────────────────────────────
@app.get("/api/metrics", tags=["system"])
def metrics():
    import json
    from app.core.config import settings
    result = {}
    for name in ["crop_metrics.json", "yield_metrics.json", "disease_metrics.json"]:
        p = settings.REPORTS_DIR / name
        if p.exists():
            result[name] = json.loads(p.read_text())
    return result


# ── Root ──────────────────────────────────────────────────────────
@app.get("/", tags=["system"])
def root():
    return {
        "name":    "AgriSmart AI API",
        "version": "2.0.0",
        "docs":    "/api/docs",
        "health":  "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    uvicorn.run("app.main:app", host=settings.API_HOST,
                port=settings.API_PORT, reload=True)
