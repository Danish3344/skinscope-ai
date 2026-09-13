from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from PIL import Image

from training.dataset import build_transforms
from training.model import create_model


def load_checkpoint(checkpoint_path: Path, device: torch.device | None = None) -> tuple[torch.nn.Module, list[str], int, torch.device]:
    selected_device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(checkpoint_path, map_location=selected_device, weights_only=False)
    class_names = list(checkpoint["class_names"])
    image_size = int(checkpoint["image_size"])
    model = create_model(len(class_names), pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(selected_device).eval()
    return model, class_names, image_size, selected_device


def predict(image: Image.Image | Path, model: torch.nn.Module, class_names: list[str], image_size: int = 224, device: torch.device | None = None, top_k: int = 3) -> dict[str, Any]:
    """Return research predictions; callers must not present them as diagnoses."""

    selected_device = device or next(model.parameters()).device
    if isinstance(image, Path):
        with Image.open(image) as opened:
            rgb = opened.convert("RGB")
    else:
        rgb = image.convert("RGB")
    tensor = build_transforms(image_size)["test"](rgb).unsqueeze(0).to(selected_device)
    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1)[0]
    count = min(top_k, len(class_names))
    values, indices = torch.topk(probabilities, count)
    ranked = [{"disease": class_names[index], "confidence": float(value)} for value, index in zip(values.cpu(), indices.cpu().tolist())]
    return {"prediction": ranked[0], "alternatives": ranked[1:], "disclaimer": "Research output only; not a medical diagnosis."}

