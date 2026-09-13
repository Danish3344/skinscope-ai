from __future__ import annotations

import logging
import sys
import time
import random
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
import torch.nn as nn
from sklearn.metrics import f1_score

from training.config import CONFIG, TrainingConfig
from training.dataset import class_weight_tensor, create_dataloaders
from training.model import create_model, freeze_backbone, parameter_groups, unfreeze_deep_blocks
from training.utils import EarlyStopping, get_device, plot_training_history, set_seed, write_json

LOGGER = logging.getLogger("training")


def dataset_gate(config: TrainingConfig = CONFIG) -> bool:
    if config.manifest_path.is_file():
        return True
    print("Training cannot start.\n")
    print(f"Dataset manifest not found:\n{config.manifest_path}\n")
    print("Please acquire a cleared dataset source and run dataset preparation first.")
    return False


def run_epoch(model: nn.Module, loader: torch.utils.data.DataLoader, criterion: nn.Module, device: torch.device, optimizer: torch.optim.Optimizer | None = None) -> tuple[float, float, float]:
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    correct = 0
    total = 0
    predictions, targets = [], []
    with torch.set_grad_enabled(training):
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            if training:
                optimizer.zero_grad(set_to_none=True)
            outputs = model(images)
            loss = criterion(outputs, labels)
            if training:
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * labels.size(0)
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += labels.size(0)
            predictions.extend(outputs.argmax(dim=1).detach().cpu().tolist()); targets.extend(labels.detach().cpu().tolist())
    return total_loss / total, correct / total, float(f1_score(targets, predictions, average="macro", zero_division=0))


def train(config: TrainingConfig = CONFIG) -> int:
    config.validate()
    if not dataset_gate(config):
        return 2
    set_seed(config.seed)
    device = get_device()
    loaders, class_names, counts = create_dataloaders(config)
    model = create_model(len(class_names), pretrained=True).to(device)
    freeze_backbone(model)
    weights = class_weight_tensor(class_names, counts, device) if config.use_class_weights else None
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(parameter_groups(model, config.learning_rate, config.classifier_learning_rate), weight_decay=config.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2, min_lr=config.min_learning_rate)
    stopper = EarlyStopping(config.early_stopping_patience)
    history: list[dict[str, float]] = []
    best_metric = -1.0
    best_accuracy = 0.0
    config.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    start_epoch = 1
    if config.checkpoint_path.is_file():
        saved = torch.load(config.checkpoint_path, map_location=device)
        if "optimizer_state_dict" in saved and "scheduler_state_dict" in saved:
            model.load_state_dict(saved["model_state_dict"])
            start_epoch = int(saved.get("epoch", 0)) + 1
            best_metric = float(saved.get("best_validation_macro_f1", -1.0))
            if start_epoch > config.frozen_epochs:
                unfreeze_deep_blocks(model, config.fine_tune_blocks)
                optimizer = torch.optim.AdamW(parameter_groups(model, config.learning_rate, config.classifier_learning_rate), weight_decay=config.weight_decay)
                scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2, min_lr=config.min_learning_rate)
            try:
                optimizer.load_state_dict(saved["optimizer_state_dict"])
                scheduler.load_state_dict(saved["scheduler_state_dict"])
            except (ValueError, KeyError, RuntimeError) as exc:
                LOGGER.warning("Optimizer/scheduler state incompatible; resetting optimizer and scheduler: %s", exc)

    for epoch in range(start_epoch, config.num_epochs + 1):
        if epoch == config.frozen_epochs + 1:
            unfreeze_deep_blocks(model, config.fine_tune_blocks)
            optimizer = torch.optim.AdamW(parameter_groups(model, config.learning_rate, config.classifier_learning_rate), weight_decay=config.weight_decay)
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2, min_lr=config.min_learning_rate)
            print(f"Fine-tuning the deepest {config.fine_tune_blocks} EfficientNet feature blocks.")
        started = time.perf_counter()
        train_loss, train_accuracy, _ = run_epoch(model, loaders["train"], criterion, device, optimizer)
        validation_loss, validation_accuracy, validation_macro_f1 = run_epoch(model, loaders["validation"], criterion, device)
        scheduler.step(validation_loss)
        learning_rate = optimizer.param_groups[0]["lr"]
        row = {"epoch": epoch, "train_loss": train_loss, "train_accuracy": train_accuracy, "validation_loss": validation_loss, "validation_accuracy": validation_accuracy, "validation_macro_f1": validation_macro_f1, "learning_rate": learning_rate}
        history.append(row)
        print(f"Epoch {epoch}/{config.num_epochs} ({time.perf_counter() - started:.1f}s)")
        print(f"Train Loss: {train_loss:.4f} | Train Accuracy: {train_accuracy:.4f}")
        print(f"Val Loss: {validation_loss:.4f} | Val Accuracy: {validation_accuracy:.4f} | Val Macro F1: {validation_macro_f1:.4f} | Learning Rate: {learning_rate:.2e}")
        improved = validation_macro_f1 > best_metric
        if improved:
            best_metric = validation_macro_f1
            best_accuracy = validation_accuracy
            torch.save({"model_state_dict": model.state_dict(), "optimizer_state_dict": optimizer.state_dict(), "scheduler_state_dict": scheduler.state_dict(), "class_names": class_names, "model_name": config.model_name, "image_size": config.image_size, "training_configuration": config.checkpoint_dict(), "best_validation_accuracy": best_accuracy, "best_validation_loss": validation_loss, "best_validation_macro_f1": best_metric, "epoch": epoch, "python_random_state": random.getstate(), "torch_random_state": torch.get_rng_state()}, config.checkpoint_path)
            write_json(config.class_names_path, class_names)
            write_json(config.model_config_path, {"model_name": config.model_name, "image_size": config.image_size, "num_classes": len(class_names), "class_names": class_names})
        write_json(config.history_json_path, history)
        plot_training_history(history, config.history_plot_path)
        stopper.bad_epochs = 0 if improved else stopper.bad_epochs + 1
        if stopper.bad_epochs >= config.early_stopping_patience:
            print(f"Early stopping after {epoch} epochs.")
            break
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    return train()


if __name__ == "__main__":
    raise SystemExit(main())
