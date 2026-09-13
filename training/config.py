from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SEED = 42
MODEL_NAME = "efficientnet_b0"
IMAGE_SIZE = 224
BATCH_SIZE = 32
NUM_EPOCHS = 30
LEARNING_RATE = 1e-4
CLASSIFIER_LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
EARLY_STOPPING_PATIENCE = 7
NUM_WORKERS = 0
FROZEN_EPOCHS = 5
FINE_TUNE_BLOCKS = 3
USE_CLASS_WEIGHTS = False
MIN_LEARNING_RATE = 1e-7


@dataclass(frozen=True)
class TrainingConfig:
    seed: int = SEED
    model_name: str = MODEL_NAME
    image_size: int = IMAGE_SIZE
    batch_size: int = BATCH_SIZE
    num_epochs: int = NUM_EPOCHS
    learning_rate: float = LEARNING_RATE
    classifier_learning_rate: float = CLASSIFIER_LEARNING_RATE
    weight_decay: float = WEIGHT_DECAY
    early_stopping_patience: int = EARLY_STOPPING_PATIENCE
    num_workers: int = NUM_WORKERS
    frozen_epochs: int = FROZEN_EPOCHS
    fine_tune_blocks: int = FINE_TUNE_BLOCKS
    use_class_weights: bool = USE_CLASS_WEIGHTS
    min_learning_rate: float = MIN_LEARNING_RATE
    manifest_path: Path = PROJECT_ROOT / "data/processed/manifest.csv"
    checkpoint_path: Path = PROJECT_ROOT / "backend/models/best_model.pth"
    class_names_path: Path = PROJECT_ROOT / "backend/models/class_names.json"
    model_config_path: Path = PROJECT_ROOT / "backend/models/model_config.json"
    history_json_path: Path = PROJECT_ROOT / "reports/training_history.json"
    history_plot_path: Path = PROJECT_ROOT / "reports/training_history.png"

    def validate(self) -> None:
        if self.image_size <= 0 or self.batch_size <= 0 or self.num_epochs <= 0:
            raise ValueError("IMAGE_SIZE, BATCH_SIZE, and NUM_EPOCHS must be positive.")
        if not 0 <= self.frozen_epochs <= self.num_epochs:
            raise ValueError("FROZEN_EPOCHS must be between zero and NUM_EPOCHS.")
        if self.learning_rate <= 0 or self.classifier_learning_rate <= 0:
            raise ValueError("Learning rates must be positive.")

    def checkpoint_dict(self) -> dict[str, object]:
        values = asdict(self)
        return {key: str(value) if isinstance(value, Path) else value for key, value in values.items()}


CONFIG = TrainingConfig()
