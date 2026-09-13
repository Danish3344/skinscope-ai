from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

ALLOWED_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MIN_DIMENSION = 32


class ImageValidationError(ValueError):
    """Raised when uploaded bytes are not a supported, safe image."""


@dataclass(frozen=True)
class NormalizedImage:
    image: Image.Image
    width: int
    height: int
    source_format: str


def validate_and_normalize_image(payload: bytes, content_type: str) -> NormalizedImage:
    """Verify encoded image bytes, enforce limits, and return an RGB copy."""

    expected_format = ALLOWED_MIME_TYPES.get(content_type.lower())
    if expected_format is None:
        raise ImageValidationError("Only JPG, JPEG, PNG, and WEBP images are supported.")

    if not payload:
        raise ImageValidationError("The uploaded image is empty.")
    if len(payload) > MAX_FILE_SIZE:
        raise ImageValidationError("The image exceeds the 10 MB size limit.")

    try:
        with Image.open(BytesIO(payload)) as candidate:
            source_format = (candidate.format or "").upper()
            width, height = candidate.size
            candidate.verify()

        if source_format != expected_format:
            raise ImageValidationError("The file content does not match its declared image type.")
        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            raise ImageValidationError(
                f"Image dimensions must be at least {MIN_DIMENSION}×{MIN_DIMENSION} pixels."
            )
        if width * height > MAX_IMAGE_PIXELS:
            raise ImageValidationError("Image dimensions are too large to process safely.")

        with Image.open(BytesIO(payload)) as candidate:
            candidate.load()
            rgb_image = candidate.convert("RGB").copy()
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ImageValidationError("The uploaded file is corrupted or is not a valid image.") from exc

    return NormalizedImage(
        image=rgb_image,
        width=width,
        height=height,
        source_format=source_format,
    )


def resize_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Return a high-quality resized RGB image for future inference code."""

    if size[0] <= 0 or size[1] <= 0:
        raise ValueError("Resize dimensions must be positive.")
    return image.convert("RGB").resize(size, Image.Resampling.LANCZOS)

