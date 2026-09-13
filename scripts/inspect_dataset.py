"""Create small per-class contact sheets from a prepared dataset manifest."""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def safe_name(label: str) -> str:
    return label.lower().replace(" ", "_")


def create_contact_sheet(label: str, rows: list[dict[str, str]], output: Path, count: int, seed: int) -> None:
    selected = random.Random(f"{seed}:{label}").sample(rows, min(count, len(rows)))
    cell_width, cell_height, caption_height = 240, 200, 34
    columns = min(4, len(selected))
    rows_count = (len(selected) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows_count * (cell_height + caption_height)), "white")
    draw = ImageDraw.Draw(sheet)

    for index, record in enumerate(selected):
        image_path = PROJECT_ROOT / record["image_path"]
        with Image.open(image_path) as image:
            tile = ImageOps.fit(image.convert("RGB"), (cell_width, cell_height), method=Image.Resampling.LANCZOS)
        x = (index % columns) * cell_width
        y = (index // columns) * (cell_height + caption_height)
        sheet.paste(tile, (x, y))
        caption = f"{record['dataset']} · {record['original_label']}"[:38]
        draw.text((x + 7, y + cell_height + 8), caption, fill="#16302b")

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG", optimize=True)
    sheet.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=PROJECT_ROOT / "data/processed/manifest.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "reports/samples")
    parser.add_argument("--samples-per-class", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.samples_per_class < 1:
        parser.error("--samples-per-class must be positive")
    if not args.manifest.is_file():
        parser.error(f"Manifest not found: {args.manifest}. Run prepare_dataset.py after adding data.")

    by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    with args.manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            image_path = PROJECT_ROOT / row["image_path"]
            if image_path.is_file():
                by_class[row["target_label"]].append(row)

    if not by_class:
        parser.error("The manifest contains no readable images.")
    for label, rows in sorted(by_class.items()):
        create_contact_sheet(label, rows, args.output / f"{safe_name(label)}.png", args.samples_per_class, args.seed)
        print(f"Created sample sheet for {label}: {min(args.samples_per_class, len(rows))} images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
