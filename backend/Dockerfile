# ==============================================================================
# Stage 1: Build & Dependencies
# ==============================================================================
FROM python:3.13-slim AS builder

WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip build wheel setuptools && \
    pip wheel --wheel-dir /build/wheels .

# ==============================================================================
# Stage 2: Production Minimal Runtime
# ==============================================================================
FROM python:3.13-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged system user & group (UID/GID 10001)
RUN groupadd --gid 10001 appgroup && \
    useradd --uid 10001 --gid appgroup --no-create-home --shell /bin/false appuser && \
    mkdir -p /app/storage /app/logs && \
    chown -R appuser:appgroup /app

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY migrations ./migrations

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health/live || exit 1

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
