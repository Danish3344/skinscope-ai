from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch


def set_seed(seed: int) -> None:
    """Seed Python, NumPy, PyTorch, and CUDA for practical reproducibility."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def get_device() -> torch.device:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        print("Training device: CUDA")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("Training device: CPU")
    return device


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class EarlyStopping:
    def __init__(self, patience: int) -> None:
        self.patience = patience
        self.best_loss = float("inf")
        self.bad_epochs = 0

    def update(self, validation_loss: float) -> bool:
        if validation_loss < self.best_loss:
            self.best_loss = validation_loss
            self.bad_epochs = 0
            return False
        self.bad_epochs += 1
        return self.bad_epochs >= self.patience


def plot_training_history(history: list[dict[str, float]], output_path: Path) -> None:
    import matplotlib.pyplot as plt

    epochs = [int(row["epoch"]) for row in history]
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot(epochs, [row["train_loss"] for row in history], label="Train")
    axes[0].plot(epochs, [row["validation_loss"] for row in history], label="Validation")
    axes[0].set(title="Loss", xlabel="Epoch", ylabel="Cross-entropy loss")
    axes[0].legend()
    axes[1].plot(epochs, [row["train_accuracy"] for row in history], label="Train")
    axes[1].plot(epochs, [row["validation_accuracy"] for row in history], label="Validation")
    axes[1].set(title="Accuracy", xlabel="Epoch", ylabel="Accuracy")
    axes[1].legend()
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)

