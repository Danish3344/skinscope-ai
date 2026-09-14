import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.ml.inference import MODEL_SERVICE, predict
from backend.locations import LocationProviderNotConfigured, NearbySearch, search_dermatologists
from backend.schemas import PredictionResponse
from backend.utils.image_utils import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    ImageValidationError,
    validate_and_normalize_image,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dermatologists", tags=["location"])
async def nearby_dermatologists(lat: float | None = None, lng: float | None = None, query: str | None = None) -> dict[str, object]:
    """Return provider-backed listings only after explicit user location request."""
    if lat is None and lng is None and not query:
        raise HTTPException(status_code=400, detail="Provide a city/location or latitude and longitude.")
    if (lat is None) != (lng is None):
        raise HTTPException(status_code=400, detail="Latitude and longitude must be provided together.")
    try:
        return {**search_dermatologists(NearbySearch(lat, lng, query)), "source": "configured_places_provider"}
    except LocationProviderNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/health", tags=["system"])
async def health_check() -> dict[str, object]:
    """Report API and one-time model loading status."""

    return {
        **MODEL_SERVICE.status(),
        "service": "skin-disease-classifier-api",
        "phase": "3B",
    }


@router.post("/predict", response_model=PredictionResponse, tags=["prediction"])
async def predict_image(image: UploadFile = File(...)) -> PredictionResponse:
    """Validate and normalize one image before handing it to the ML boundary."""

    content_type = (image.content_type or "").lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPG, JPEG, PNG, and WEBP images are supported.",
        )

    try:
        payload = await image.read(MAX_FILE_SIZE + 1)
    finally:
        await image.close()

    if len(payload) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The image exceeds the 10 MB size limit.",
        )

    try:
        normalized = validate_and_normalize_image(payload, content_type)
    except ImageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="skinscope_", suffix=".png", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            normalized.image.save(temporary, format="PNG")

        inference_result = predict(temporary_path)
        return PredictionResponse(
            **inference_result,
            image={
                "width": normalized.width,
                "height": normalized.height,
                "format": normalized.source_format,
            },
        )
    except OSError as exc:
        logger.exception("Temporary image processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The image could not be processed.",
        ) from exc
    finally:
        normalized.image.close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
