# syntax=docker/dockerfile:1

# ---------------------------------------------------------
# Stage 1: Build Python dependency wheels
# ---------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .

RUN python -m pip wheel \
    --no-cache-dir \
    --wheel-dir /wheels \
    -r requirements.txt


# ---------------------------------------------------------
# Stage 2: Minimal runtime image
# ---------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Secure GitOps Task API" \
      org.opencontainers.image.description="FastAPI application for a secure GitOps platform" \
      org.opencontainers.image.source="https://github.com/baqir-ops/secure-gitops-app"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Create an unprivileged application user.
RUN groupadd --gid 10001 appgroup \
    && useradd \
       --uid 10001 \
       --gid appgroup \
       --create-home \
       --shell /usr/sbin/nologin \
       appuser

COPY --from=builder /wheels /wheels
COPY requirements.txt .

RUN python -m pip install \
    --no-cache-dir \
    --no-index \
    --find-links=/wheels \
    -r requirements.txt \
    && rm -rf /wheels

COPY --chown=appuser:appgroup app ./app

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s \
            --timeout=3s \
            --start-period=10s \
            --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

STOPSIGNAL SIGTERM

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
