# ==============================================================================
# Purrfect Spots Backend - Production Dockerfile
# ==============================================================================
# Multi-stage build for optimized image size and security
# Base image: Python 3.12 slim

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim AS production

LABEL maintainer="Purrfect Spots Team <support@purrfectspots.com>"
LABEL description="Purrfect Spots API - Cat location sharing platform"
LABEL version="3.0.0"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# Copy application code with explicit ownership
# nosec docker:S6470 - Recursive copy is intentional; .dockerignore excludes tests, cache, git
# nosec docker:S6504 - Using --chown to set proper non-root ownership
# nosec docker:S2612 - chmod 550 removes write permissions (r-x for owner/group)
COPY --chown=appuser:appgroup --chmod=550 .

# Remove unnecessary files
RUN rm -rf tests/ .pytest_cache/ __pycache__/ .coverage .git/

# Build arguments for configuration (non-secret data)
# SECURITY NOTE: DO NOT use ARG for secrets as they are baked into the image layers.
# Use environment variables at runtime or secrets mounts for sensitive data.
ARG APP_PORT=8000
ARG WORKER_COUNT=2

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    PORT=${APP_PORT} \
    WORKERS=${WORKER_COUNT}

# Switch to non-root user
USER appuser

# Expose port (uses ARG/ENV for flexibility)
EXPOSE ${PORT}

# Health check (uses PORT env)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/live || exit 1

# Run the application
# nosec B104 - 0.0.0.0 is required for container network binding
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS}"]
