from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_recall_fscore_support

from training.config import CONFIG
from training.dataset import create_dataloaders
from training.inference import load_checkpoint
from training.utils import write_json


def main() -> int:
    if not CONFIG.checkpoint_path.is_file():
        print(f"Evaluation cannot start.\n\nCheckpoint not found:\n{CONFIG.checkpoint_path}")
        return 2
    if not CONFIG.manifest_path.is_file():
        print(f"Evaluation cannot start.\n\nDataset manifest not found:\n{CONFIG.manifest_path}")
        return 2
    loaders, manifest_classes, _ = create_dataloaders(CONFIG)
    model, class_names, _, device = load_checkpoint(CONFIG.checkpoint_path)
    if class_names != manifest_classes:
        raise ValueError("Checkpoint classes do not match the current manifest.")
    predictions: list[int] = []
    targets: list[int] = []
    with torch.inference_mode():
        for images, labels in loaders["test"]:
            predictions.extend(model(images.to(device)).argmax(dim=1).cpu().tolist())
            targets.extend(labels.tolist())
    labels = list(range(len(class_names)))
    report_text = classification_report(targets, predictions, labels=labels, target_names=class_names, zero_division=0)
    precision, recall, f1, support = precision_recall_fscore_support(targets, predictions, labels=labels, zero_division=0)
    metrics = {"accuracy": accuracy_score(targets, predictions), "macro_f1": f1_score(targets, predictions, average="macro"), "weighted_f1": f1_score(targets, predictions, average="weighted"), "per_class": {name: {"precision": float(precision[i]), "recall": float(recall[i]), "f1": float(f1[i]), "support": int(support[i])} for i, name in enumerate(class_names)}}
    reports = CONFIG.history_json_path.parent
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "classification_report.txt").write_text(report_text, encoding="utf-8")
    write_json(reports / "test_metrics.json", metrics)
    matrix = confusion_matrix(targets, predictions, labels=labels)
    figure, axis = plt.subplots(figsize=(10, 9))
    image = axis.imshow(matrix, cmap="Blues")
    axis.set(xticks=labels, yticks=labels, xticklabels=class_names, yticklabels=class_names, xlabel="Predicted", ylabel="Actual", title="Held-out test confusion matrix")
    plt.setp(axis.get_xticklabels(), rotation=45, ha="right")
    figure.colorbar(image, ax=axis)
    figure.tight_layout()
    figure.savefig(reports / "confusion_matrix.png", dpi=170)
    plt.close(figure)
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

