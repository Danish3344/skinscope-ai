from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app

client = TestClient(app)


def make_image_bytes(image_format: str = "PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 48), color=(126, 82, 69)).save(buffer, format=image_format)
    return buffer.getvalue()


def test_predict_accepts_valid_image_and_returns_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    temporary_path: Path | None = None

    def capture_inference_path(image_path: Path) -> dict[str, object]:
        nonlocal temporary_path
        temporary_path = image_path
        assert image_path.is_file()
        with Image.open(image_path) as normalized:
            assert normalized.mode == "RGB"
            assert normalized.format == "PNG"
        return {
            "success": True,
            "status": "model_not_loaded",
            "prediction": None,
            "confidence": None,
            "alternatives": [],
            "disease_info": None,
            "disclaimer": None,
            "message": "ML model has not been trained or installed yet.",
        }

    monkeypatch.setattr("backend.api.routes.predict", capture_inference_path)
    response = client.post(
        "/predict",
        files={"image": ("lesion.png", make_image_bytes(), "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "model_not_loaded",
        "prediction": None,
        "confidence": None,
        "alternatives": [],
        "disease_info": None,
        "disclaimer": None,
        "message": "ML model has not been trained or installed yet.",
        "image": {"width": 64, "height": 48, "format": "PNG"},
    }
    assert temporary_path is not None
    assert not temporary_path.exists()


@pytest.mark.parametrize(
    ("filename", "content_type", "payload"),
    [
        ("notes.txt", "text/plain", b"not an image"),
        ("document.pdf", "application/pdf", b"%PDF-1.4"),
        ("program.exe", "application/octet-stream", b"MZ"),
    ],
)
def test_predict_rejects_unsupported_files(filename: str, content_type: str, payload: bytes) -> None:
    response = client.post("/predict", files={"image": (filename, payload, content_type)})

    assert response.status_code == 415


def test_predict_rejects_oversized_file() -> None:
    response = client.post(
        "/predict",
        files={"image": ("large.png", b"x" * (10 * 1024 * 1024 + 1), "image/png")},
    )

    assert response.status_code == 413


def test_predict_requires_image_field() -> None:
    response = client.post("/predict")

    assert response.status_code == 422


def test_predict_rejects_corrupted_image() -> None:
    response = client.post(
        "/predict",
        files={"image": ("corrupted.png", b"this is not really a png", "image/png")},
    )

    assert response.status_code == 422
    assert "corrupted" in response.json()["detail"]


def test_predict_rejects_mime_content_mismatch() -> None:
    response = client.post(
        "/predict",
        files={"image": ("renamed.png", make_image_bytes("JPEG"), "image/png")},
    )

    assert response.status_code == 422
    assert "does not match" in response.json()["detail"]
