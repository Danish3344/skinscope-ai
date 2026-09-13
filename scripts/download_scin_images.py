"""Resumable downloader for the official SCIN public GCS image objects."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import pathlib
import time
import urllib.request
import urllib.parse

BUCKET = "https://storage.googleapis.com/dx-scin-public-data/"


def metadata_paths(root: pathlib.Path) -> list[str]:
    import csv

    paths: set[str] = set()
    with (root / "scin_cases.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for col in ("image_1_path", "image_2_path", "image_3_path"):
                value = (row.get(col) or "").strip()
                if value:
                    paths.add(value)
    return sorted(paths)


def download_one(args: tuple[str, pathlib.Path]) -> tuple[str, int, str]:
    object_name, destination = args
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return object_name, destination.stat().st_size, "present"
    url = BUCKET + urllib.parse.quote(object_name, safe="/")
    temporary = destination.with_suffix(destination.suffix + ".part")
    existing = temporary.stat().st_size if temporary.exists() else 0
    for attempt in range(1, 6):
        try:
            request = urllib.request.Request(url)
            if existing:
                request.add_header("Range", f"bytes={existing}-")
            with urllib.request.urlopen(request, timeout=120) as response:
                # Never append a full 200 response to a partial file.
                append = existing > 0 and response.status == 206
                if existing and not append:
                    existing = 0
                mode = "ab" if append else "wb"
                with temporary.open(mode) as out:
                    while chunk := response.read(1024 * 1024):
                        out.write(chunk)
            temporary.replace(destination)
            return object_name, destination.stat().st_size, "downloaded"
        except Exception:
            if attempt == 5:
                raise
            time.sleep(min(60, 2 ** (attempt - 1)))
            existing = temporary.stat().st_size if temporary.exists() else 0
    raise RuntimeError(object_name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    root = pathlib.Path("data/raw/scin")
    image_root = root / "dataset" / "images"
    paths = metadata_paths(root)
    jobs = [(name, image_root / pathlib.Path(name).name) for name in paths]
    present = sum(1 for _, p in jobs if p.exists() and p.stat().st_size > 0)
    print(json.dumps({"expected_objects": len(jobs), "present_objects": present, "remaining_objects": len(jobs) - present}))
    completed = present
    downloaded_bytes = sum(p.stat().st_size for _, p in jobs if p.exists() and p.stat().st_size > 0)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        futures = [pool.submit(download_one, job) for job in jobs if not (job[1].exists() and job[1].stat().st_size > 0)]
        for future in concurrent.futures.as_completed(futures):
            name, size, _ = future.result()
            completed += 1
            downloaded_bytes += size
            if completed % 100 == 0 or completed == len(jobs):
                print(json.dumps({"completed": completed, "total": len(jobs), "bytes": downloaded_bytes}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
