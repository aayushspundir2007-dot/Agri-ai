# AgriSmart AI — API Documentation

Base URL: `http://localhost:8000`
Interactive docs: `http://localhost:8000/api/docs`

All prediction endpoints require a JWT Bearer token obtained from `/api/auth/login`.

---

## Authentication

### POST /api/auth/login

**Request:**
```json
{ "username": "admin", "password": "admin123" }
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "username": "admin",
  "name": "Admin User",
  "role": "admin"
}
```

**Response 401:**
```json
{ "detail": "Invalid username or password" }
```

---

### POST /api/auth/logout
No body required. Returns `{ "detail": "Logged out successfully" }`.
Client should discard the token.

---

## Predictions

All prediction endpoints require: `Authorization: Bearer <token>`

---

### POST /api/predict/crop

**Request:**
```json
{
  "N": 90, "P": 42, "K": 43,
  "temperature": 25.0,
  "humidity": 80.0,
  "ph": 6.5,
  "rainfall": 100.0
}
```

**Field validation:**
| Field | Type | Range |
|---|---|---|
| N | float | 0–200 |
| P | float | 0–200 |
| K | float | 0–250 |
| temperature | float | -5–55 |
| humidity | float | 0–100 |
| ph | float | 0–14 |
| rainfall | float | 0–5000 |

**Response 200:**
```json
{
  "crop": "Jute",
  "probabilities": {
    "Jute": 0.98, "Papaya": 0.01, "Banana": 0.005,
    "Mango": 0.003, "Coconut": 0.002
  },
  "model": "RandomForest"
}
```

---

### POST /api/predict/yield

**Request:**
```json
{
  "area": "India",
  "item": "Wheat",
  "year": 2010,
  "rainfall": 1083.0,
  "pesticides": 55000.0,
  "temperature": 24.0
}
```

**Response 200:**
```json
{
  "yield_hgha": 25751.14,
  "area": "India",
  "item": "Wheat",
  "year": 2010,
  "model": "ExtraTrees"
}
```

---

### POST /api/predict/disease

**Request:** `multipart/form-data` with field `file` (image/jpeg or image/png)

```bash
curl -X POST http://localhost:8000/api/predict/disease \
  -H "Authorization: Bearer <token>" \
  -F "file=@leaf.jpg"
```

**Response 200:**
```json
{
  "predicted_class": "Tomato___healthy",
  "confidence": 0.97,
  "top5": {
    "Tomato___healthy": 0.97,
    "Tomato___Early_blight": 0.015,
    "Tomato___Late_blight": 0.008,
    "Tomato___Bacterial_spot": 0.005,
    "Tomato___Leaf_Mold": 0.002
  },
  "model": "HistGradientBoosting"
}
```

---

## System endpoints

### GET /api/health
```json
{
  "status": "ok",
  "models_loaded": { "crop": true, "yield": true, "disease": true },
  "uptime_seconds": 3600.0,
  "version": "2.0.0"
}
```

### GET /api/analytics
```json
{
  "total_predictions": { "crop": 12, "yield": 5, "disease": 3 },
  "average_latency_ms": { "crop": 45.2, "yield": 120.5, "disease": 85.1 },
  "average_confidence": { "crop": 0.94, "disease": 0.88 },
  "top5_crops": { "Jute": 4, "Rice": 3, "Wheat": 2, "Maize": 2, "Cotton": 1 },
  "uptime_seconds": 3600.0
}
```

### GET /api/metrics
Returns raw training metrics from `reports/*.json`.

---

## User Management (admin only)

### GET /api/users
Returns list of all users.

### POST /api/users
```json
{ "username": "john", "name": "John Smith", "password": "pass123", "role": "viewer" }
```

### DELETE /api/users/{username}
Returns 204 on success. Cannot delete your own account.

---

## Error codes

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | Deleted |
| 401 | Unauthorized — missing or invalid token |
| 403 | Forbidden — insufficient role |
| 404 | Not found |
| 409 | Conflict — username already exists |
| 422 | Validation error — check field ranges |
| 503 | Model not loaded — restart API |
