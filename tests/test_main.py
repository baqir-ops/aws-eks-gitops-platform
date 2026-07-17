import pytest
from fastapi.testclient import TestClient

from app.main import TASKS, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_application_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent one test from affecting another."""

    TASKS.clear()
    monkeypatch.delenv("FORCE_FAILURE", raising=False)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "secure-gitops-task-api",
        "status": "running",
        "version": "1.0.0",
    }


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_forced_health_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORCE_FAILURE", "true")

    response = client.get("/health")

    assert response.status_code == 500
    assert response.json()["detail"] == "Simulated health failure"


def test_readiness() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_create_and_list_task() -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "Learn GitOps",
            "completed": False,
        },
    )

    assert created.status_code == 201
    assert created.json() == {
        "id": 1,
        "title": "Learn GitOps",
        "completed": False,
    }

    listed = client.get("/tasks")

    assert listed.status_code == 200
    assert listed.json() == [created.json()]


def test_empty_task_title_is_rejected() -> None:
    response = client.post(
        "/tasks",
        json={
            "title": "",
            "completed": False,
        },
    )

    assert response.status_code == 422


def test_prometheus_metrics() -> None:
    client.get("/")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "app_http_requests_total" in response.text
    assert "app_http_request_duration_seconds" in response.text
