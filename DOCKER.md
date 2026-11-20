# AgriSmart AI — Docker Guide

## Quick start

```bash
# 1. Copy env file
cp .env.example .env

# 2. Start everything (API + Streamlit + Frontend + Jenkins + Selenium)
docker-compose up -d

# 3. Check services
docker-compose ps

# 4. View logs
docker-compose logs -f api
```

**Services:**
| Service | URL |
|---|---|
| FastAPI backend | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/api/docs |
| Streamlit UI | http://localhost:8501 |
| HTML frontend | http://localhost:3000/pages/login.html |
| Jenkins | http://localhost:8080 |

---

## Build the image manually

```bash
# production image (multi-stage)
docker build -t agrismart-api:latest .

# test runner image
docker build -f Dockerfile.test -t agrismart-test:latest .
```

---

## Run just the API

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/users.json:/app/users.json \
  --env-file .env \
  agrismart-api:latest
```

---

## Run tests in Docker

```bash
# isolated test environment
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# or run manually
docker run --rm \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/reports:/app/reports \
  agrismart-test:latest
```

---

## Stop all services

```bash
docker-compose down

# also remove volumes (Jenkins data)
docker-compose down -v
```

---

## Environment variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET` | `agrismart-dev-secret...` | Change in production |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_HOURS` | `24` | Token lifetime |
| `API_PORT` | `8000` | FastAPI port |
| `STREAMLIT_API_URL` | `http://localhost:8000` | API URL for Streamlit |

---

## Volumes

| Volume | Purpose |
|---|---|
| `./models:/app/models` | Trained ML models (.joblib) |
| `./reports:/app/reports` | Metrics JSON + test reports |
| `./users.json:/app/users.json` | User credentials |
| `jenkins_home` | Jenkins configuration & build history |
