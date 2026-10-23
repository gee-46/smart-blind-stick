# ==============================================================================
# Production Dockerfile - Smart Blind Stick Cloud API
# Supports Public HTTPS Hosting (Render, Railway, Fly.io, AWS, DigitalOcean)
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATA_DIR=/app/data \
    AI_VISION_MODEL_PATH=/app/models/yolov8n.pt

# Install minimal OS dependencies for compilation and OpenCV compatibility
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user for secure production execution
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install Python dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir "ultralytics>=8.2.0,<8.3.0"

# Create persistent storage directory and models directory
# Pre-fetch official YOLOv8n weights into /app/models during container build
RUN mkdir -p /app/data /app/models && \
    curl -sSL -o /app/models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt && \
    chown -R appuser:appgroup /app/data /app/models

# Copy application source code
COPY --chown=appuser:appgroup . .

# Declare persistent volume mount point
VOLUME ["/app/data"]

# Switch to non-root user
USER appuser

# Expose dynamic application port
EXPOSE 8000

# Docker healthcheck against backend /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Production startup: binds to 0.0.0.0 and honors $PORT from hosting provider
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
