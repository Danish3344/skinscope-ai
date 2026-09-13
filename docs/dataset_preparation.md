# Dataset preparation

The preparation tools validate and organize local data; they do not download images or train a model.

## Active Kaggle workflow

The active candidate source is Kaggle's `ismailpromus/skin-diseases-image-dataset`, stored outside Fitzpatrick17k:

```text
data/raw/kaggle_skin_diseases/
├── skin-diseases-image-dataset.zip
└── IMG_CLASSES/
    ├── Atopic Dermatitis/
    ├── Basal Cell Carcinoma/
    ├── Eczema/
    ├── Melanoma/
    └── ...
```

First configure Kaggle credentials locally. Do not paste a token into chat.

```text
C:\Users\pawan\OneDrive\Documents\ChatGPT\skin\.kaggle\kaggle.json
```

or:

```text
%USERPROFILE%\.kaggle\kaggle.json
```

Then run:

```powershell
python scripts\download_kaggle_dataset.py
python scripts\download_kaggle_dataset.py --extract
```

The helper downloads through Kaggle's API, validates ZIP integrity, prints archive structure, and extracts only after inspection. If credentials are missing it exits cleanly with code 2.

Important: the Kaggle page currently shows `Data files © Original Authors`, which is not a clear open ML-training license. The config therefore keeps `training_allowed: false` for `kaggle_skin_diseases`. Do not change that flag until the license has been reviewed and accepted for the project's research use.

Once license clearance is recorded and the extracted folder exists, preparation will read `IMG_CLASSES` directly, validate images, remove exact duplicates, split by SHA-256 groups, and materialize `data/train`, `data/validation`, and `data/test`.

## Acquire and place the source

Follow the [official Fitzpatrick17k download instructions](https://github.com/mattgroh/fitzpatrick17k#download-the-dataset). The publisher exposes the metadata CSV and asks users to request image access through its form because some original URLs are broken.

Place the obtained files exactly as follows:

```text
data/raw/fitzpatrick17k/
├── fitzpatrick17k.csv
└── images/
    ├── <md5hash or url_alphanum filename>
    └── ...
```

Images may have `.jpg`, `.jpeg`, `.png`, `.webp`, or no suffix when their filename is the metadata MD5. Do not commit these files.

Current status: the official CSV and upstream attribution README are present, but the `images/` directory is absent. Obtain the complete archive through the publisher's official request route before running preparation. Do not scrape the original atlas URLs, and do not create an empty `images/` directory as evidence of acquisition.

### Manual archive acquisition

The official repository does not publish a stable archive filename or direct public archive URL. It instructs users to:

1. Open the publisher's [Fitzpatrick17k image access form](https://forms.gle/4fS35Kg8x9pkG2Bn9).
2. Submit the requested identity, affiliation, intended-use, and contact information truthfully.
3. Contact the dataset team as instructed and wait for the authorized archive link.
4. Download the archive from that supplied link only. For a consistent local name, save it as `data/raw/fitzpatrick17k/fitzpatrick17k-images.zip` if it is a ZIP file; otherwise preserve the actual archive extension.
5. Do not overwrite `fitzpatrick17k.csv` or `UPSTREAM_README.md`.

No official archive checksum or canonical archive filename is published in the repository. Record the download URL, received filename, byte size, and any checksum included in the access email before extraction. Do not rename a non-ZIP archive with a `.zip` suffix.

After the authorized archive has been placed in `data/raw/fitzpatrick17k/`, return to Codex for archive-integrity checks and safe extraction. If extracting manually, use a staging directory first rather than extracting directly over `images/`; archive nesting is not documented and must be inspected before final placement.

After extraction has been verified and the image files are directly discoverable under `data/raw/fitzpatrick17k/images/`, run:

```powershell
python scripts\prepare_dataset.py
python scripts\inspect_dataset.py
python -m pytest -q
python -m compileall backend scripts
```

## Install and run

From the repository root in PowerShell:

```powershell
python -m pip install -r requirements-data.txt
python scripts\prepare_dataset.py
python scripts\inspect_dataset.py
```

The script exits without producing a manifest if configured metadata or usable mapped images are missing.

Do not run preparation merely because the metadata CSV exists. First confirm that the image directory contains the authorized archive and compare its file count against the 16,577 metadata records. In the current state, all 16,577 image references are unavailable locally and the pipeline has intentionally not generated outputs.

## Pipeline behavior

For every metadata row, preparation:

1. normalizes the source label and applies only `data/class_mapping.json`;
2. resolves the image by safe basename using configured metadata filename columns;
3. verifies image decoding and dimensions with Pillow;
4. rejects unsupported formats and reports suspicious images below 64 pixels on either side;
5. calculates SHA-256 and removes exact duplicates;
6. groups related records, assigns reproducible 70/15/15 splits, and balances mapped labels reasonably;
7. hard-links images into ImageFolder-style directories when supported, otherwise copies them;
8. writes the manifest, statistics, and class-distribution chart.

Outputs are:

```text
data/processed/manifest.csv
data/train/<target_class>/...
data/validation/<target_class>/...
data/test/<target_class>/...
reports/dataset_statistics.json
reports/dataset_distribution.png
reports/samples/<target_class>.png
```

The manifest includes patient or lesion columns only when the configured source actually supplies them. IDs are never invented.

## Leakage prevention

The split grouping priority is:

```text
patient_id → lesion_id → SHA-256 image hash
```

If a patient ID exists, every record for that patient remains in one split. Otherwise, a lesion/case ID is used. Without either identifier—as in the published Fitzpatrick17k CSV—exact duplicates are grouped by content hash. That last fallback does **not** detect different photographs of the same lesion, so this dataset retains a documented residual leakage risk.

The splitter uses seed 42 and greedily assigns complete groups while targeting per-class ratios. Running it on unchanged inputs is deterministic.

## Quality reports and visual review

`dataset_statistics.json` records totals for valid, missing, corrupt, suspiciously small, duplicate, and unsupported images, along with unsupported label counts and limited issue examples. Nothing is silently relabeled.

`inspect_dataset.py` selects up to eight deterministic random samples per prepared class. Review every contact sheet for:

- source-label mismatch;
- non-skin or diagram images;
- watermarks, text, rulers, or framing shortcuts;
- inconsistent clinical versus dermoscopic modality;
- near-duplicates not caught by exact hashing;
- skin-tone and acquisition diversity.

Do not proceed to training when a mapped class looks visually incoherent.

## Configuration

- `data/dataset_config.json` controls sources, filenames, extensions, ratios, seed, minimum dimensions, and ImageFolder materialization.
- `data/class_mapping.json` is the single mapping authority. Unsupported targets deliberately have empty source-label lists.

When adding a new source, verify its official licence first, add its metadata schema to `sources`, and only then add source-specific mappings. Never map an unknown or merely similar condition to fill a target class.
