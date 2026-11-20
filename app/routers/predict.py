"""Prediction router — /api/predict/crop, /yield, /disease."""
import io
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image

from app.core.ml_loader import ml
from app.core.monitoring import monitor
from app.models.auth import get_current_user
from app.models.schemas import (
    CropRequest, CropResponse,
    DiseaseResponse,
    YieldRequest, YieldResponse,
    TokenData,
)

router = APIRouter(prefix="/api/predict", tags=["predictions"])


@router.post("/crop", response_model=CropResponse)
def predict_crop(
    body: CropRequest,
    _: TokenData = Depends(get_current_user),
):
    if ml.crop_model is None:
        raise HTTPException(status_code=503, detail="Crop model not loaded")
    t0 = time.time()
    crop, probs = ml.predict_crop(
        body.N, body.P, body.K,
        body.temperature, body.humidity, body.ph, body.rainfall,
    )
    latency = (time.time() - t0) * 1000
    conf = probs.get(crop, 0.0)
    monitor.log_prediction("crop", body.model_dump(), crop, latency, conf)
    return CropResponse(crop=crop, probabilities=probs)


@router.post("/yield", response_model=YieldResponse)
def predict_yield(
    body: YieldRequest,
    _: TokenData = Depends(get_current_user),
):
    if ml.yield_model is None:
        raise HTTPException(status_code=503, detail="Yield model not loaded")
    t0 = time.time()
    val = ml.predict_yield(
        body.area, body.item, body.year,
        body.rainfall, body.pesticides, body.temperature,
    )
    latency = (time.time() - t0) * 1000
    monitor.log_prediction("yield", body.model_dump(), val, latency)
    return YieldResponse(
        yield_hgha=round(val, 2),
        area=body.area, item=body.item, year=body.year,
    )


@router.post("/disease", response_model=DiseaseResponse)
async def predict_disease(
    file: UploadFile = File(...),
    _: TokenData = Depends(get_current_user),
):
    if ml.disease_model is None:
        raise HTTPException(status_code=503, detail="Disease model not loaded")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="File must be an image")
    t0 = time.time()
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    pred_class, confidence, top5 = ml.predict_disease(image)
    latency = (time.time() - t0) * 1000
    monitor.log_prediction("disease", {"filename": file.filename},
                           pred_class, latency, confidence)
    return DiseaseResponse(
        predicted_class=pred_class,
        confidence=confidence,
        top5=top5,
    )
