from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_loaded": True,
        "service": "skin-disease-classifier-api",
        "phase": "3B",
        "model_name": "efficientnet_b0",
        "num_classes": 4,
    }


def test_health_cors_for_configured_frontend() -> None:
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
