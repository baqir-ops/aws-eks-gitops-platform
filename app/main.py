import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field

app = FastAPI(
    title="Secure GitOps Task API",
    description="Sample API deployed through the Secure GitOps Platform",
    version="1.1.0",
)

HTTP_REQUESTS = Counter(
    "app_http_requests_total",
    "Total HTTP requests processed by the application",
    ["method", "path", "status"],
)

HTTP_LATENCY = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["path"],
)

# Intentionally in-memory for this platform demonstration.
TASKS: list[dict[str, Any]] = []


class TaskCreate(BaseModel):
    """Request model for creating a task."""

    title: str = Field(min_length=1, max_length=200)
    completed: bool = False


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    """Record request count and latency for Prometheus."""

    path = request.url.path

    with HTTP_LATENCY.labels(path=path).time():
        response = await call_next(request)

    HTTP_REQUESTS.labels(
        method=request.method,
        path=path,
        status=str(response.status_code),
    ).inc()

    return response


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "secure-gitops-task-api",
        "status": "running",
        "version": "1.1.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness endpoint: should Kubernetes restart this container?"""

    if os.getenv("FORCE_FAILURE", "false").lower() == "true":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulated health failure",
        )

    return {"status": "healthy"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Readiness endpoint: should Kubernetes send traffic here?"""

    return {"status": "ready"}


@app.get("/tasks")
def list_tasks() -> list[dict[str, Any]]:
    return TASKS


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate) -> dict[str, Any]:
    task_record = {
        "id": len(TASKS) + 1,
        **task.model_dump(),
    }

    TASKS.append(task_record)
    return task_record


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
