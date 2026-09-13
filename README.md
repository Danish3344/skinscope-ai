# Skin Disease Classification System

An educational/research full-stack application for classifying skin-condition images. Phase 2 provides a secure image intake and processing pipeline. It does **not** perform classification yet and must not be used for medical diagnosis.

## Phase 2 features

- FastAPI application with `GET /health`, `POST /predict`, and interactive API documentation
- React, Vite, Tailwind CSS, Axios, and React Router frontend
- Validated click/drag-and-drop uploads for JPG, JPEG, PNG, and WEBP up to 10 MB
- Browser camera capture with rear-camera preference, retake, and graceful error handling
- Responsive preview with dimensions, file size, removal, and camera retake
- Pillow content verification, RGB normalization, safe temporary processing, and cleanup
- Explicit placeholder inference response without fabricated disease predictions
- Visible backend status, request/error states, and medical disclaimer
- Environment-based API and CORS configuration
- Backend endpoint and CORS tests

## Architecture

```text
Browser (React/Vite) ── multipart image ──> FastAPI validation
        │                                      │
 upload / camera                         Pillow normalization
                                               │
                                      temporary image (deleted)
                                               │
                                      Phase 3 inference boundary
```

Phase 3 will introduce ML-specific preprocessing, a trained PyTorch classifier, and evaluation reports. Location and medical-report features remain future extension points.

## Prerequisites on Windows

- Python 3.11 or newer
- Node.js 20 or newer (includes npm)

Verify them with `python --version`, `node --version`, and `npm --version`.

## Backend setup

From the project root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000/docs` for API documentation. Test health directly:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Run backend tests from the project root:

```powershell
python -m pytest backend\tests -q
```

## Frontend setup

In a second PowerShell terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. The status badge should change from **API checking** to **API online** while the backend is running.

For a production build:

```powershell
cd frontend
npm run build
```

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | API readiness and model integration status |
| POST | `/predict` | Validate and normalize a multipart `image`; return Phase 3 integration status |

Successful Phase 2 requests return `status: "model_not_loaded"`, null prediction/confidence values, and verified image metadata. No medical result is generated.

## Project structure

```text
backend/          FastAPI application and tests
frontend/         React/Vite application
training/         Future model training pipeline
scripts/          Future dataset preparation utilities
data/             Ignored raw/processed dataset locations
reports/          Future evaluation outputs
docs/             Project documentation
```

## Dataset and ML roadmap

No dataset is downloaded and no fake model is included. Phase 3A audited Fitzpatrick17k as a provisional, non-commercial research source under CC BY-NC-SA 3.0. Its official metadata supports eight of the ten requested targets; Atopic Dermatitis and Warts remain unavailable and must not be fabricated. See [dataset strategy](docs/dataset_strategy.md) and [dataset preparation](docs/dataset_preparation.md).

```text
Dataset
   ↓
Dataset audit and licence review
   ↓
Verified class mapping
   ↓
Image validation and exact deduplication
   ↓
Grouped train / validation / test split
   ↓
Manifest, statistics, and sample galleries
   ↓
Future ML training (not started)
```

The active dataset candidate is now Kaggle's [Skin Diseases Image Dataset](https://www.kaggle.com/datasets/ismailpromus/skin-diseases-image-dataset), stored under `data/raw/kaggle_skin_diseases`. Kaggle credentials are not configured in this environment yet, and the public page lists the license as `Data files © Original Authors`, so training is blocked until the archive is downloaded, inspected, and the license is cleared for this research use.

Configure Kaggle credentials locally, never in chat:

```text
C:\Users\pawan\OneDrive\Documents\ChatGPT\skin\.kaggle\kaggle.json
```

Then run:

```powershell
python scripts\download_kaggle_dataset.py
python scripts\download_kaggle_dataset.py --extract
```

Fitzpatrick17k remains available as a future source. Its metadata is present, but its image archive is not. Request those images through the [publisher's official access instructions](https://github.com/mattgroh/fitzpatrick17k#download-the-dataset) if needed.

After a dataset has images and license clearance, run:

```powershell
python -m pip install -r requirements-data.txt
python scripts\prepare_dataset.py
python scripts\inspect_dataset.py
```

The resulting `data/train`, `data/validation`, and `data/test` trees are compatible with PyTorch `ImageFolder`. Dataset images, generated reports, and future model weights are excluded from Git.

Current dataset gate: **zero usable local Kaggle images; preparation and training are blocked**. The Kaggle candidate appears to support only four direct target mappings from public class names: Atopic Dermatitis, Basal Cell Carcinoma, Melanoma, and Eczema. Mixed labels are not used automatically. See the strategy document for license and mapping limitations.

The complete EfficientNet-B0 training, evaluation, and top-3 inference infrastructure is implemented but remains behind this gate. See [training documentation](docs/training.md). Running `python training\train.py` before preparation exits cleanly without creating weights or fake reports.

## Limitations

- Camera access depends on browser support, device permissions, and a secure context (`localhost` or HTTPS).
- The 10 MB limit is enforced in the browser and backend; encoded images must also satisfy dimension limits.
- No model, disease predictions, disease information, doctor lookup, or PDF reports are included yet.
- CORS permits only the configured `FRONTEND_URL`.

## Medical disclaimer

This project is for educational and research purposes only. Its future outputs will be probabilistic model predictions, not diagnoses or treatment advice. Consult a qualified dermatologist for assessment of any skin concern.
