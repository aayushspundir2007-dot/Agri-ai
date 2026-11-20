# ═══════════════════════════════════════════════
# AgriSmart AI — Multi-stage Production Dockerfile
# ═══════════════════════════════════════════════

# ── Stage 1: builder ────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /install

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install \
    fastapi \
    "uvicorn[standard]" \
    "python-jose[cryptography]" \
    "passlib[bcrypt]" \
    python-multipart \
    httpx \
    scikit-learn \
    pandas \
    numpy \
    joblib \
    Pillow \
    plotly \
    streamlit \
    python-dotenv \
    matplotlib

# ── Stage 2: runtime ────────────────────────────
FROM python:3.11-slim AS runtime

# non-root user for security
RUN groupadd -r agrismart && useradd -r -g agrismart agrismart

WORKDIR /app

# copy installed packages from builder
COPY --from=builder /install /usr/local

# copy application code
COPY app/           ./app/
COPY streamlit_app/ ./streamlit_app/
COPY src/           ./src/
COPY .streamlit/    ./.streamlit/
COPY .env.example   ./.env.example

# copy artefacts (populated at runtime via volume mounts)
RUN mkdir -p models reports
COPY models/.gitkeep            ./models/
COPY models/disease_classes.json ./models/ 2>/dev/null || true
COPY reports/.gitkeep           ./reports/

# copy users file
COPY users.json ./users.json

# ownership
RUN chown -R agrismart:agrismart /app

USER agrismart

# FastAPI on 8000, Streamlit on 8501
EXPOSE 8000 8501

# healthcheck on FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" \
    || exit 1

# default: start FastAPI
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
