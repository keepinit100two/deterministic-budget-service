from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ops_ping_endpoint() -> None:
    response = client.get("/ops/ping")

    assert response.status_code in (200, 401, 403, 503)

    if response.status_code == 503:
        assert response.json() == {"detail": "OPS_API_KEY not configured"}


def test_ingest_api_smoke() -> None:
    payload = {
        "event_type": "task_requested",
        "source": "api",
        "actor": "baseline-test",
        "payload": {
            "message": "baseline ingest smoke test"
        },
        "metadata": {
            "test_case": "baseline_regression"
        },
    }

    response = client.post(
        "/ingest/api",
        json=payload,
        headers={"Idempotency-Key": "baseline-smoke-test-001"},
    )

    assert response.status_code == 200

    body = response.json()

    # Protect the existing response contract at a high level
    assert "event" in body
    assert "decision" in body

    # Protect basic event structure
    assert "event_id" in body["event"]
    assert body["event"]["event_type"] == "task_requested"
    assert body["event"]["source"] == "api"

    # Protect basic decision structure
    assert "decision_id" in body["decision"]
    assert "route" in body["decision"]
    assert "reason" in body["decision"]