"""Validate, deduplicate, split, and manifest configured dermatology datasets.

This script never downloads data and never trains a model.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import logging
import os
import random
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

LOGGER = logging.getLogger("prepare_dataset")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPLITS = ("train", "validation", "test")


@dataclass
class Record:
    source_path: Path
    dataset: str
    original_label: str
    target_label: str
    patient_id: str
    lesion_id: str
    content_hash: str
    width: int
    height: int
    image_format: str
    split: str = ""
    output_path: Path | None = None


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def normalized_label(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def mapping_index(mapping: dict[str, Any]) -> dict[tuple[str, str], str]:
    index: dict[tuple[str, str], str] = {}
    for target, details in mapping.items():
        dataset = details.get("dataset")
        if not dataset or details.get("mapping_type") != "direct":
            continue
        for label in details.get("dataset_labels", []):
            key = (dataset, normalized_label(label))
            if key in index:
                raise ValueError(f"Ambiguous mapping for {key}: {index[key]} and {target}")
            index[key] = target
    return index


def locate_image(row: dict[str, str], source: dict[str, Any], extensions: list[str]) -> Path | None:
    root = PROJECT_ROOT / source["root"] / source["image_directory"]
    for column in source["filename_columns"]:
        value = (row.get(column) or "").strip()
        if not value:
            continue
        candidate = root / Path(value).name
        if candidate.is_file():
            return candidate
        if candidate.suffix:
            continue
        for extension in extensions:
            extended = candidate.with_suffix(extension)
            if extended.is_file():
                return extended
    return None


def imagefolder_records(source: dict[str, Any], extensions: list[str]) -> list[dict[str, str]]:
    root = PROJECT_ROOT / source["root"] / source["image_directory"]
    if not root.is_dir():
        raise FileNotFoundError(root)
    records: list[dict[str, str]] = []
    for class_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for path in sorted(class_dir.rglob("*")):
            if not path.is_file():
                continue
            records.append({
                "label": class_dir.name,
                "image_path": path.relative_to(root).as_posix(),
            })
    return records


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_image(path: Path, minimum_dimension: int) -> tuple[int, int, str]:
    with Image.open(path) as image:
        width, height = image.size
        image_format = (image.format or "").upper()
        image.verify()
    if width < minimum_dimension or height < minimum_dimension:
        raise ValueError(f"suspicious dimensions {width}x{height}")
    if image_format not in {"JPEG", "PNG", "WEBP"}:
        raise ValueError(f"unsupported encoded format {image_format or '<unknown>'}")
    return width, height, image_format


def group_key(record: Record) -> str:
    if record.patient_id:
        return f"{record.dataset}:patient:{record.patient_id}"
    if record.lesion_id:
        return f"{record.dataset}:lesion:{record.lesion_id}"
    return f"hash:{record.content_hash}"


def assign_grouped_splits(records: list[Record], ratios: dict[str, float], seed: int) -> None:
    """Greedily balance classes while keeping patient/lesion groups intact."""

    grouped: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        grouped[group_key(record)].append(record)

    rng = random.Random(seed)
    groups = list(grouped.values())
    rng.shuffle(groups)
    groups.sort(key=len, reverse=True)

    totals = Counter(record.target_label for record in records)
    desired = {
        split: {label: totals[label] * ratio for label in totals}
        for split, ratio in ratios.items()
    }
    assigned: dict[str, Counter[str]] = {split: Counter() for split in SPLITS}

    for group in groups:
        group_counts = Counter(record.target_label for record in group)
        scores: dict[str, float] = {}
        for split in SPLITS:
            deficit_score = sum(
                max(desired[split][label] - assigned[split][label], 0) * count / totals[label]
                for label, count in group_counts.items()
            )
            size_penalty = sum(assigned[split].values()) / max(ratios[split], 0.001) / max(len(records), 1)
            scores[split] = deficit_score - (0.01 * size_penalty)
        chosen = max(SPLITS, key=lambda split: (scores[split], -SPLITS.index(split)))
        for record in group:
            record.split = chosen
        assigned[chosen].update(group_counts)


def safe_class_directory(label: str) -> str:
    return label.lower().replace(" ", "_")


def materialize(record: Record) -> Path:
    destination_dir = PROJECT_ROOT / "data" / record.split / safe_class_directory(record.target_label)
    destination_dir.mkdir(parents=True, exist_ok=True)
    format_suffix = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}[record.image_format]
    destination = destination_dir / f"{record.content_hash[:20]}{format_suffix}"
    if not destination.exists():
        try:
            os.link(record.source_path, destination)
        except OSError:
            shutil.copy2(record.source_path, destination)
    return destination


def write_manifest(records: list[Record], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["image_path", "dataset", "original_label", "target_label", "split"]
    if any(record.patient_id for record in records):
        fields.append("patient_id")
    if any(record.lesion_id for record in records):
        fields.append("lesion_id")
    fields.extend(["sha256", "width", "height"])

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in sorted(records, key=lambda item: (item.split, item.target_label, str(item.source_path))):
            row: dict[str, Any] = {
                "image_path": record.output_path.relative_to(PROJECT_ROOT).as_posix() if record.output_path else record.source_path.relative_to(PROJECT_ROOT).as_posix(),
                "dataset": record.dataset,
                "original_label": record.original_label,
                "target_label": record.target_label,
                "split": record.split,
                "sha256": record.content_hash,
                "width": record.width,
                "height": record.height,
            }
            if "patient_id" in fields:
                row["patient_id"] = record.patient_id
            if "lesion_id" in fields:
                row["lesion_id"] = record.lesion_id
            writer.writerow(row)


def create_distribution(records: list[Record], path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Install requirements-data.txt to generate the distribution chart.") from exc
    counts = Counter(record.target_label for record in records)
    labels = sorted(counts)
    figure, axis = plt.subplots(figsize=(11, 6))
    axis.bar(labels, [counts[label] for label in labels], color="#2f7d6d")
    axis.set_title("Prepared dataset distribution")
    axis.set_ylabel("Images")
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160)
    plt.close(figure)


def prepare(config_path: Path, mapping_path: Path) -> int:
    config = load_json(config_path)
    mapping = load_json(mapping_path)
    index = mapping_index(mapping)
    extensions = [extension.lower() for extension in config["image_extensions"]]
    quality = Counter()
    unsupported_labels: Counter[str] = Counter()
    issue_examples: dict[str, list[str]] = defaultdict(list)
    records: list[Record] = []
    seen_hashes: dict[str, Path] = {}

    active_dataset = config.get("active_dataset")
    sources = [
        source for source in config["sources"]
        if active_dataset in {None, source["name"]}
    ]
    if not sources:
        LOGGER.error("No configured source matches active_dataset=%r", active_dataset)
        return 2

    for source in sources:
        if source.get("training_allowed") is False:
            LOGGER.error(
                "Dataset %s is blocked because its license status has not been cleared for training: %s",
                source["name"],
                source.get("license_status", "unknown"),
            )
            return 4

        if source.get("type") == "scin_metadata":
            cases_path = PROJECT_ROOT / source["root"] / source["metadata"]
            labels_path = PROJECT_ROOT / source["root"] / source["labels"]
            with cases_path.open(newline="", encoding="utf-8-sig") as cf, labels_path.open(newline="", encoding="utf-8-sig") as lf:
                cases = {r["case_id"]: r for r in csv.DictReader(cf)}
                labels = {r["case_id"]: r for r in csv.DictReader(lf)}
            rows = []
            for case_id, row in cases.items():
                try:
                    weighted = ast.literal_eval(labels[case_id]["weighted_skin_condition_label"])
                    label = max(weighted, key=weighted.get)
                except (KeyError, ValueError, SyntaxError):
                    label = ""
                for col in source.get("image_path_columns", []):
                    if row.get(col):
                        rows.append({"label": label, "image_path": row[col], "case_id": case_id})
            label_column = "label"
        elif source.get("type", "metadata_csv") == "imagefolder":
            try:
                rows = imagefolder_records(source, extensions)
            except FileNotFoundError as exc:
                LOGGER.error("Missing image folder: %s", exc)
                return 2
            label_column = "label"
        else:
            metadata_path = PROJECT_ROOT / source["root"] / source["metadata"]
            if not metadata_path.is_file():
                LOGGER.error("Missing metadata: %s", metadata_path)
                return 2
            handle = metadata_path.open(newline="", encoding="utf-8-sig")
            rows = csv.DictReader(handle)
            label_column = source["label_column"]

        try:
            for row in rows:
                quality["total_records"] += 1
                original_label = (row.get(label_column) or "").strip()
                target = index.get((source["name"], normalized_label(original_label)))
                if not target:
                    quality["unsupported_images"] += 1
                    unsupported_labels[original_label or "<missing>"] += 1
                    continue
                if source.get("type") == "scin_metadata":
                    image_path = PROJECT_ROOT / source["root"] / source["image_directory"] / Path(row["image_path"]).name
                elif source.get("type", "metadata_csv") == "imagefolder":
                    image_path = PROJECT_ROOT / source["root"] / source["image_directory"] / row["image_path"]
                    if image_path.suffix.lower() not in extensions:
                        quality["unsupported_format_files"] += 1
                        unsupported_labels[f"{original_label}::{image_path.suffix or '<no extension>'}"] += 1
                        continue
                else:
                    image_path = locate_image(row, source, extensions)
                if image_path is None:
                    quality["missing_images"] += 1
                    if len(issue_examples["missing"]) < 20:
                        issue_examples["missing"].append(str(row))
                    continue
                try:
                    width, height, image_format = validate_image(image_path, int(config["minimum_dimension"]))
                    digest = file_hash(image_path)
                except (UnidentifiedImageError, OSError) as exc:
                    quality["corrupted_images"] += 1
                    if len(issue_examples["corrupted"]) < 20:
                        issue_examples["corrupted"].append(f"{image_path}: {exc}")
                    continue
                except ValueError as exc:
                    quality["suspicious_small_images"] += 1
                    if len(issue_examples["small"]) < 20:
                        issue_examples["small"].append(f"{image_path}: {exc}")
                    continue
                if digest in seen_hashes:
                    quality["duplicate_images"] += 1
                    if len(issue_examples["duplicates"]) < 20:
                        issue_examples["duplicates"].append(f"{image_path} == {seen_hashes[digest]}")
                    continue
                seen_hashes[digest] = image_path
                records.append(Record(
                    source_path=image_path,
                    dataset=source["name"],
                    original_label=original_label,
                    target_label=target,
                    patient_id=(row.get(source.get("case_id_column")) or row.get(source.get("patient_id_column")) or "").strip() if (source.get("case_id_column") or source.get("patient_id_column")) else "",
                    lesion_id=(row.get(source.get("lesion_id_column")) or "").strip() if source.get("lesion_id_column") else "",
                    content_hash=digest,
                    width=width,
                    height=height,
                    image_format=image_format,
                ))
        finally:
            if source.get("type", "metadata_csv") not in {"imagefolder", "scin_metadata"}:
                handle.close()

    if not records:
        LOGGER.error("No usable mapped images were found; no outputs were generated.")
        return 3

    ratios = {"train": config["train_ratio"], "validation": config["validation_ratio"], "test": config["test_ratio"]}
    if abs(sum(ratios.values()) - 1.0) > 1e-9:
        raise ValueError("Split ratios must sum to 1.0")
    assign_grouped_splits(records, ratios, int(config["seed"]))
    if config.get("materialize_imagefolder", True):
        for record in records:
            record.output_path = materialize(record)

    write_manifest(records, PROJECT_ROOT / "data/processed/manifest.csv")
    split_counts = Counter(record.split for record in records)
    statistics = {
        "total_records": quality["total_records"],
        "total_images": len(records),
        "train_images": split_counts["train"],
        "validation_images": split_counts["validation"],
        "test_images": split_counts["test"],
        "class_counts": dict(sorted(Counter(record.target_label for record in records).items())),
        "dataset_sources": dict(sorted(Counter(record.dataset for record in records).items())),
        "corrupted_images": quality["corrupted_images"],
        "missing_images": quality["missing_images"],
        "suspicious_small_images": quality["suspicious_small_images"],
        "duplicate_images": quality["duplicate_images"],
        "unsupported_images": quality["unsupported_images"],
        "unsupported_format_files": quality["unsupported_format_files"],
        "unsupported_labels": dict(unsupported_labels.most_common()),
        "issue_examples": dict(issue_examples),
    }
    statistics_path = PROJECT_ROOT / "reports/dataset_statistics.json"
    statistics_path.parent.mkdir(parents=True, exist_ok=True)
    statistics_path.write_text(json.dumps(statistics, indent=2), encoding="utf-8")
    create_distribution(records, PROJECT_ROOT / "reports/dataset_distribution.png")

    print("Dataset quality report")
    print("----------------------")
    print(f"Total records: {quality['total_records']}")
    print(f"Valid images: {len(records)}")
    print(f"Corrupted: {quality['corrupted_images']}")
    print(f"Missing: {quality['missing_images']}")
    print(f"Suspicious small: {quality['suspicious_small_images']}")
    print(f"Unsupported classes: {quality['unsupported_images']}")
    print(f"Duplicates: {quality['duplicate_images']}")
    print(f"Final usable images: {len(records)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "data/dataset_config.json")
    parser.add_argument("--mapping", type=Path, default=PROJECT_ROOT / "data/class_mapping.json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    return prepare(args.config.resolve(), args.mapping.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
