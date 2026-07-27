# ---- Build stage ----
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Runtime stage ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser api ./api
COPY --chown=appuser:appuser app.py .

USER appuser

# Puerto por defecto de Cloud Run
ENV PORT=8080

# Gunicorn con worker de Uvicorn para alta concurrencia asíncrona.
# --workers 1: en Cloud Run se recomienda 1 worker por instancia (GCP gestiona el escalado).
# --timeout 0: desactiva el timeout de gunicorn para dejar que Cloud Run gestione el ciclo de vida.
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 0 api.main:app
