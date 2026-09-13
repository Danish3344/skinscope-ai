from collections import defaultdict
from pathlib import Path

from PIL import Image

from scripts.prepare_dataset import Record, assign_grouped_splits, imagefolder_records, mapping_index, validate_image


def make_record(index: int, label: str, patient: str = "") -> Record:
    return Record(
        source_path=Path(f"image-{index}.jpg"),
        dataset="fixture",
        original_label=label.lower(),
        target_label=label,
        patient_id=patient,
        lesion_id="",
        content_hash=f"{index:064x}",
        width=100,
        height=100,
        image_format="JPEG",
    )


def test_mapping_index_normalizes_source_labels() -> None:
    mapping = {
        "Basal Cell Carcinoma": {
            "dataset": "fixture",
            "dataset_labels": ["basal-cell_carcinoma"],
            "mapping_type": "direct",
        },
        "Unavailable": {
            "dataset": None,
            "dataset_labels": [],
            "mapping_type": "unavailable",
        },
        "Possible": {
            "dataset": "fixture",
            "dataset_labels": ["mixed category"],
            "mapping_type": "possible",
        },
    }

    assert mapping_index(mapping) == {("fixture", "basal cell carcinoma"): "Basal Cell Carcinoma"}


def test_grouped_split_never_leaks_patients_and_is_reproducible() -> None:
    records = [
        make_record(index, "Acne" if index % 2 else "Psoriasis", patient=f"patient-{index // 2}")
        for index in range(30)
    ]
    ratios = {"train": 0.7, "validation": 0.15, "test": 0.15}
    assign_grouped_splits(records, ratios, seed=42)
    first_assignment = [record.split for record in records]

    patient_splits: dict[str, set[str]] = defaultdict(set)
    for record in records:
        patient_splits[record.patient_id].add(record.split)
    assert all(len(splits) == 1 for splits in patient_splits.values())
    assert set(first_assignment) == {"train", "validation", "test"}

    for record in records:
        record.split = ""
    assign_grouped_splits(records, ratios, seed=42)
    assert [record.split for record in records] == first_assignment


def test_image_validation_reports_dimensions_and_format(tmp_path: Path) -> None:
    image_path = tmp_path / "valid.png"
    Image.new("RGB", (80, 64), "purple").save(image_path)

    assert validate_image(image_path, minimum_dimension=64) == (80, 64, "PNG")


def test_imagefolder_records_reads_class_directories(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "data/raw/kaggle_skin_diseases/IMG_CLASSES/Atopic Dermatitis"
    root.mkdir(parents=True)
    (root / "sample.jpg").write_bytes(b"placeholder")
    monkeypatch.setattr("scripts.prepare_dataset.PROJECT_ROOT", tmp_path)

    rows = imagefolder_records(
        {
            "root": "data/raw/kaggle_skin_diseases",
            "image_directory": "IMG_CLASSES",
        },
        [".jpg"],
    )

    assert rows == [{"label": "Atopic Dermatitis", "image_path": "Atopic Dermatitis/sample.jpg"}]
