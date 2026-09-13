from pathlib import Path

import pandas as pd
import torch
from PIL import Image

from training.config import CONFIG, TrainingConfig
from training.dataset import deterministic_class_names
from training.inference import predict
from training.model import create_model
from training.train import train


def test_training_configuration_is_valid() -> None:
    CONFIG.validate()
    assert CONFIG.image_size > 0
    assert CONFIG.batch_size > 0
    assert CONFIG.num_epochs > 0


def test_efficientnet_output_matches_dynamic_class_count() -> None:
    model = create_model(num_classes=5, pretrained=False)
    output = model(torch.zeros(1, 3, 224, 224))

    assert output.shape == (1, 5)


def test_missing_manifest_exits_cleanly(tmp_path: Path, capsys) -> None:
    config = TrainingConfig(manifest_path=tmp_path / "missing.csv")

    assert train(config) == 2
    output = capsys.readouterr().out
    assert "Training cannot start" in output
    assert "Dataset manifest not found" in output


def test_class_indices_follow_config_deterministically(tmp_path: Path) -> None:
    dataset_config = tmp_path / "dataset_config.json"
    dataset_config.write_text('{"target_classes": ["Zeta", "Alpha", "Beta"]}', encoding="utf-8")
    frame = pd.DataFrame({"target_label": ["Beta", "Zeta", "Alpha", "Beta"]})

    first = deterministic_class_names(frame, dataset_config)
    second = deterministic_class_names(frame.sample(frac=1, random_state=99), dataset_config)

    assert first == second == ["Zeta", "Alpha", "Beta"]


class FixedLogitModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.zeros(1))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return torch.tensor([[0.1, 2.5, 1.0]], device=inputs.device).repeat(inputs.shape[0], 1)


def test_top_k_inference_with_lightweight_model() -> None:
    result = predict(
        Image.new("RGB", (300, 300), "tan"),
        FixedLogitModel(),
        ["Acne", "Psoriasis", "Eczema"],
        top_k=3,
    )

    assert result["prediction"]["disease"] == "Psoriasis"
    assert [row["disease"] for row in result["alternatives"]] == ["Eczema", "Acne"]
    assert "not a medical diagnosis" in result["disclaimer"]

