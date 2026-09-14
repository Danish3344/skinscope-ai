from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from backend.ml.disease_info import get_disease_info

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHECKPOINT = PROJECT_ROOT / "backend/models/best_model.pth"
LOGGER = logging.getLogger(__name__)


class ModelService:
    """Load a valid checkpoint once, while keeping an absent model non-fatal."""

    def __init__(self, checkpoint_path: Path = DEFAULT_CHECKPOINT) -> None:
        self.checkpoint_path = checkpoint_path
        self.model: Any = None
        self.class_names: list[str] = []
        self.image_size = 224
        self.device: Any = None
        self.model_name: str | None = None
        self.load_error: str | None = None

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def initialize(self) -> None:
        if self.loaded or not self.checkpoint_path.is_file():
            return
        try:
            import torch
            from training.inference import load_checkpoint

            checkpoint = torch.load(self.checkpoint_path, map_location="cpu", weights_only=False)
            self.model_name = str(checkpoint.get("model_name", "efficientnet_b0"))
            self.model, self.class_names, self.image_size, self.device = load_checkpoint(self.checkpoint_path)
        except Exception as exc:
            self.load_error = str(exc)
            LOGGER.exception("Model checkpoint could not be loaded")

    def status(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": "ok", "model_loaded": self.loaded}
        if self.loaded:
            payload.update(model_name=self.model_name, num_classes=len(self.class_names))
        return payload

    def predict(self, image_path: Path) -> dict[str, Any]:
        if not image_path.is_file():
            raise FileNotFoundError("The normalized image is unavailable for inference.")
        if not self.loaded:
            return {
                "success": True,
                "status": "model_not_loaded",
                "prediction": None,
                "confidence": None,
                "alternatives": [],
                "message": "ML model has not been trained or installed yet.",
            }

        from training.inference import predict as model_predict

        # Return the primary prediction plus three ranked alternatives (all four classes).
        result = model_predict(image_path, self.model, self.class_names, self.image_size, self.device, top_k=4)
        primary = result["prediction"]
        return {
            "success": True,
            "status": "model_loaded",
            "prediction": primary,
            "confidence": primary["confidence"],
            "alternatives": result["alternatives"],
            "disease_info": get_disease_info(str(primary["disease"])),
            "disclaimer": "This AI prediction is for educational/research purposes only. It is not a medical diagnosis. Please consult a qualified dermatologist for professional evaluation.",
            "message": "Research prediction generated. This is not a medical diagnosis.",
            "model_name": self.model_name,
            "class_names": self.class_names,
            "image_size": self.image_size,
        }


MODEL_SERVICE = ModelService()
MODEL_SERVICE.initialize()


def predict(image_path: Path) -> dict[str, Any]:
    """Stable backend inference boundary used by the API route."""

    return MODEL_SERVICE.predict(image_path)
