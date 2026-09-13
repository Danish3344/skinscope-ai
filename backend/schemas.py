from typing import Literal

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    success: bool
    status: Literal["model_not_loaded", "model_loaded"]
    prediction: dict[str, str | float] | None = None
    confidence: float | None = None
    alternatives: list[dict[str, str | float]] = Field(default_factory=list)
    disease_info: dict[str, object] | None = None
    disclaimer: str | None = None
    message: str
    image: dict[str, int | str]
