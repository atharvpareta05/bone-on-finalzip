# CareLens Clinical Decision-Support Backend
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies for OpenCV/Pillow & health probe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase, config, and artifacts
COPY backend /app/backend
COPY outputs /app/outputs
COPY app_uploads /app/app_uploads
COPY app_data.sqlite3* /app/

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    UPLOAD_DIR=/app/app_uploads \
    DATABASE_URL=sqlite:////app/app_data.sqlite3

EXPOSE 8000

# Loud healthcheck: fails container deploy if model fails to load or DB is unreachable
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
