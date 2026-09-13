"""Download and safely inspect the configured Kaggle skin-disease dataset.

The script requires local Kaggle credentials. Do not paste tokens into chat.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_SLUG = "ismailpromus/skin-diseases-image-dataset"
TARGET_DIR = PROJECT_ROOT / "data/raw/kaggle_skin_diseases"
ARCHIVE_PATH = TARGET_DIR / "skin-diseases-image-dataset.zip"
LOCAL_KAGGLE_DIR = PROJECT_ROOT / ".kaggle"


def credential_dir() -> Path | None:
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return Path(os.environ.get("KAGGLE_CONFIG_DIR", str(LOCAL_KAGGLE_DIR)))

    configured = os.environ.get("KAGGLE_CONFIG_DIR")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.append(LOCAL_KAGGLE_DIR)
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidates.append(Path(user_profile) / ".kaggle")

    for directory in candidates:
        token = directory / "kaggle.json"
        if token.is_file():
            return directory
    return None


def inspect_archive(path: Path) -> dict[str, int | list[str]]:
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise zipfile.BadZipFile(f"Corrupted member: {bad_member}")
        names = archive.namelist()
    image_extensions = (".jpg", ".jpeg", ".png", ".webp")
    image_count = sum(name.lower().endswith(image_extensions) for name in names)
    top_level = sorted({name.split("/")[0] for name in names if "/" in name})
    return {
        "members": len(names),
        "image_members": image_count,
        "top_level_entries": top_level[:40],
    }


def extract_archive(path: Path, target: Path) -> None:
    staging = target / "_extract_staging"
    if staging.exists():
        raise FileExistsError(f"Refusing to reuse staging directory: {staging}")
    staging.mkdir(parents=True)
    with zipfile.ZipFile(path) as archive:
        archive.extractall(staging)

    image_root = target / "IMG_CLASSES"
    candidates = [path for path in staging.rglob("IMG_CLASSES") if path.is_dir()]
    if not candidates:
        raise FileNotFoundError("Archive did not contain an IMG_CLASSES directory.")
    if image_root.exists():
        raise FileExistsError(f"Refusing to overwrite existing dataset directory: {image_root}")
    candidates[0].rename(image_root)
    shutil.rmtree(staging)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", action="store_true", help="Extract the inspected archive into IMG_CLASSES.")
    args = parser.parse_args()

    credentials = credential_dir()
    if credentials is None:
        print("Kaggle credentials were not found.")
        print("")
        print("Create an API token in Kaggle Account settings, then place it locally as one of:")
        print(f"  {LOCAL_KAGGLE_DIR / 'kaggle.json'}")
        print("  %USERPROFILE%\\.kaggle\\kaggle.json")
        print("")
        print("Do not paste the token into chat.")
        return 2

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE_PATH.is_file():
        env = {**os.environ, "KAGGLE_CONFIG_DIR": str(credentials)}
        command = [
            sys.executable,
            "-m",
            "kaggle",
            "datasets",
            "download",
            "-d",
            DATASET_SLUG,
            "-p",
            str(TARGET_DIR),
        ]
        completed = subprocess.run(command, env=env, check=False)
        if completed.returncode != 0:
            print("Kaggle download failed. Confirm credentials, dataset access, and accepted Kaggle terms.")
            return completed.returncode

    summary = inspect_archive(ARCHIVE_PATH)
    print(f"Archive: {ARCHIVE_PATH}")
    print(f"Size bytes: {ARCHIVE_PATH.stat().st_size}")
    print(f"Members: {summary['members']}")
    print(f"Image members: {summary['image_members']}")
    print(f"Top-level entries: {summary['top_level_entries']}")

    if args.extract:
        extract_archive(ARCHIVE_PATH, TARGET_DIR)
        print(f"Extracted image folders to: {TARGET_DIR / 'IMG_CLASSES'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
