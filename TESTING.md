# AgriSmart AI — Testing Guide

## Test stack
- **pytest** + **pytest-cov** + **pytest-html** — unit & integration
- **Playwright** (Python) — end-to-end browser tests
- **httpx TestClient** (FastAPI) — integration without a live server

---

## Run all tests

```bash
# activate venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# run everything
pytest

# run only unit tests (fast, no server needed)
pytest -m unit

# run only integration tests
pytest -m integration

# run only E2E
pytest -m e2e

# skip slow tests
pytest -m "not slow"
```

---

## Test reports

After each run, open:

| Report | Path |
|---|---|
| HTML test report | `reports/test_report.html` |
| Coverage HTML | `reports/coverage_html/index.html` |
| Coverage XML (CI) | `reports/coverage.xml` |
| JUnit XML (Jenkins) | `reports/junit.xml` |

---

## Unit tests (`app/tests/unit/`)

| File | Tests | What's covered |
|---|---|---|
| `test_crop_model.py` | 10 | Model load, predict, 22 classes, proba sum, parametrized inputs |
| `test_yield_model.py` | 10 | Load, positive value, India/France ranges, sparse fix, parametrized |
| `test_disease_model.py` | 10 | Load, 10 classes, 1120 feature dims, confidence range, top-5 |
| `test_auth.py` | 14 | Bcrypt/SHA-256 hash, JWT create/decode, expiry, login endpoint |

**Run:**
```bash
pytest app/tests/unit/ -v
```

---

## Integration tests (`app/tests/integration/`)

Require the FastAPI TestClient (no live server needed).

| File | Tests | Endpoints covered |
|---|---|---|
| `test_api_crop.py`    | 9 | POST /api/predict/crop |
| `test_api_yield.py`   | 9 | POST /api/predict/yield |
| `test_api_disease.py` | 8 | POST /api/predict/disease |

**Run:**
```bash
pytest app/tests/integration/ -v
```

---

## E2E tests (`app/tests/e2e/`)

Require Playwright + a browser. Run against the HTML frontend (`frontend/pages/`).

| File | Tests | What's covered |
|---|---|---|
| `test_login_flow.py`  | 9 | Login, logout, error states, role-based nav |
| `test_crop_flow.py`   | 8 | Crop page load, inputs, button, result, bars |
| `test_disease_flow.py`| 7 | Disease page, drop zone, upload, analyze |

**Install browser (once):**
```bash
.venv\Scripts\python.exe -m playwright install chromium
```

**Run:**
```bash
pytest app/tests/e2e/ -v
```

---

## Run via Docker

```bash
# Build test image
docker build -f Dockerfile.test -t agrismart-test .

# Run unit + integration only
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Check reports
open reports/test_report.html
```

---

## Coverage threshold

The project requires **≥ 70%** coverage. `pytest.ini` enforces this via:
```ini
--cov-fail-under=70
```

To check coverage without failing:
```bash
pytest --cov=app --cov-report=term-missing --no-cov-on-fail
```
