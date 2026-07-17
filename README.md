# Secure GitOps Task API

A FastAPI application built for the Secure End-to-End GitOps Platform project.

## Features

- Liveness endpoint: `/health`
- Readiness endpoint: `/ready`
- Create and list tasks using `/tasks`
- Prometheus metrics endpoint: `/metrics`
- Controlled failure testing using `FORCE_FAILURE`
- Ruff linting and pytest unit tests

## Run Locally

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-dev.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Open Swagger UI:

    http://127.0.0.1:8000/docs

## Quality Checks

    ruff check app tests
    pytest -v

## Controlled Failure Test

Start the API in failure mode:

    FORCE_FAILURE=true uvicorn app.main:app --host 0.0.0.0 --port 8000

Test the probes:

    curl -i http://127.0.0.1:8000/health
    curl -i http://127.0.0.1:8000/ready

Expected behavior:

- `/health` returns HTTP `500`
- `/ready` returns HTTP `200`
