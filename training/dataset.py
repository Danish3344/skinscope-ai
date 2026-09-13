from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms

from training.config import CONFIG, PROJECT_ROOT, TrainingConfig

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_transforms(image_size: int = CONFIG.image_size) -> dict[str, transforms.Compose]:
    resize_size = int(round(image_size * 256 / 224))
    return {
        "train": transforms.Compose([
            transforms.Resize(resize_size),
            transforms.RandomResizedCrop(image_size, scale=(0.85, 1.0), ratio=(0.9, 1.1)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.12, contrast=0.12, saturation=0.08, hue=0.02),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]),
        "validation": transforms.Compose([
            transforms.Resize(resize_size),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]),
        "test": transforms.Compose([
            transforms.Resize(resize_size),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]),
    }


def deterministic_class_names(frame: pd.DataFrame, dataset_config_path: Path | None = None) -> list[str]:
    present = set(frame["target_label"].dropna().astype(str))
    config_path = dataset_config_path or PROJECT_ROOT / "data/dataset_config.json"
    configured = json.loads(config_path.read_text(encoding="utf-8"))["target_classes"]
    ordered = [name for name in configured if name in present]
    ordered.extend(sorted(present.difference(ordered)))
    return ordered


class ManifestDataset(Dataset[tuple[torch.Tensor, int]]):
    def __init__(self, frame: pd.DataFrame, class_names: list[str], transform: transforms.Compose) -> None:
        self.frame = frame.reset_index(drop=True)
        self.class_to_index = {name: index for index, name in enumerate(class_names)}
        self.transform = transform

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        row = self.frame.iloc[index]
        path = PROJECT_ROOT / str(row["image_path"])
        with Image.open(path) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, self.class_to_index[str(row["target_label"])]


def load_manifest(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    required = {"image_path", "target_label", "split"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Manifest is missing columns: {', '.join(sorted(missing))}")
    if frame.empty:
        raise ValueError("Dataset manifest is empty.")
    return frame


def create_dataloaders(config: TrainingConfig = CONFIG) -> tuple[dict[str, DataLoader], list[str], Counter[str]]:
    frame = load_manifest(config.manifest_path)
    class_names = deterministic_class_names(frame)
    if len(class_names) < 2:
        raise ValueError("Training requires at least two classes in the manifest.")
    transform_map = build_transforms(config.image_size)
    loaders: dict[str, DataLoader] = {}
    for split in ("train", "validation", "test"):
        split_frame = frame[frame["split"] == split]
        if split_frame.empty:
            raise ValueError(f"Manifest split '{split}' is empty.")
        dataset = ManifestDataset(split_frame, class_names, transform_map[split])
        sampler = None
        if split == "train":
            labels = [class_names.index(str(v)) for v in split_frame["target_label"]]
            counts = Counter(labels)
            sample_weights = [1.0 / counts[label] for label in labels]
            sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)
        loaders[split] = DataLoader(
            dataset,
            batch_size=config.batch_size,
            shuffle=False,
            sampler=sampler,
            num_workers=config.num_workers,
            pin_memory=torch.cuda.is_available(),
        )
    counts = Counter(frame[frame["split"] == "train"]["target_label"].astype(str))
    return loaders, class_names, counts


def class_weight_tensor(class_names: list[str], counts: Counter[str], device: torch.device) -> torch.Tensor:
    total = sum(counts.values())
    weights = [total / (len(class_names) * counts[name]) for name in class_names]
    return torch.tensor(weights, dtype=torch.float32, device=device)
