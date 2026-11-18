# CodeGuard AI

Machine learning source-code vulnerability classification for an academic security-review workflow. A React/Monaco frontend calls a FastAPI service backed by a **real, locally trained, calibrated five-class classifier**. No paid API, fabricated metrics, regex classifier, or code execution is used.

This is a research baseline, not a production vulnerability detector. Its training corpus is a small, synthetic Juliet subset. A "Safe Code" prediction does not prove security. See [dataset limitations](docs/DATASET.md).

## Features and scope

- Dashboard, source editor, file upload, result explanations, class probabilities, and saved evaluation reports.
- Classes: 0 SQL Injection; 1 Buffer Overflow; 2 Cross-Site Scripting; 3 Integer Overflow; 4 Safe Code.
- Evaluated language scope: **C memory and integer issues; C++ memory issues; Java SQL injection and XSS**. Python/JavaScript are intentionally unavailable until appropriately labeled data and evaluation are added.
- Abstention for low confidence, unfamiliar features, insufficient context, or a leading category outside the language's training scope.
- Optional SQLite scan history containing only result metadata; disabled by default.
- Missing models produce a clear unavailable response, never a mock prediction.

## Architecture and files

Browser → FastAPI → shared normalization → TF-IDF → calibrated classifier → probabilities and category guidance. Data preparation, model training, and inference are independent of the UI. [Architecture and API contract](docs/ARCHITECTURE.md).

```text
backend/app/       FastAPI, category guidance, optional SQLAlchemy history
backend/tests/     ML, API, privacy, and integration tests
frontend/src/      React pages, Monaco editor, typed Axios client, UI tests
ml/prepare.py     Juliet extraction, provenance, deduplication and groups
ml/train.py       Candidate selection, calibration, evaluation and plots
ml/inference.py   Artifact loading, probabilities and abstention
ml/artifacts/     Generated model, metadata, splits and confusion matrix
scripts/          Verified dataset downloader and live HTTP smoke test
docs/             Architecture, dataset card and validation record
```

Stack: Python 3.14 (tested environment), scikit-learn, NumPy, Pandas, Joblib, Matplotlib/Seaborn, FastAPI/Pydantic, Uvicorn, SQLAlchemy, React 19, Vite 7, Tailwind 4, Axios, Monaco, Recharts, Lucide, pytest and Vitest. Use **Python 3.14** with the supplied full dependency lock. Supporting older Python releases requires resolving compatible transitive versions. Python 3.14 matches the supplied Docker image. Node 24 is recommended for the checked lockfile. CodeBERT/PyTorch/Transformers fine-tuning is optional and **not implemented or claimed** in this baseline release.

## Local setup — Windows PowerShell

Run from the project root. An internet connection is needed once for dependencies and approximately 220 MB of NIST archives. No credentials are needed. curl is included with current Windows releases.

```powershell
Set-Location 'C:\Python-ML files\CodeGuard-AI'
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.lock
.\.venv\Scripts\python scripts\download_data.py
.\.venv\Scripts\python -m ml.prepare
.\.venv\Scripts\python -m ml.train
Set-Location frontend
npm ci
Set-Location ..
```

If pip downloads are slow and uv is installed: `uv pip install --python .venv\Scripts\python.exe -r backend\requirements.lock`. An optional checksum-verifying curl downloader is also supplied: run `.\.venv\Scripts\python scripts\download_wheels.py`, then install with `.\.venv\Scripts\python -m pip install --no-index --find-links .cache\wheels -r backend\requirements.lock`.

Start the backend in terminal 1, from the project root:

```powershell
$env:MODEL_DIR = 'ml/artifacts'
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

If your prompt currently ends in `\backend>`, return to the project root first:

```powershell
Set-Location ..
..\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

The module name must be started from the project root; running the same module command while remaining inside `backend` produces `ModuleNotFoundError: No module named 'backend'`.

Start the frontend in terminal 2:

```powershell
Set-Location 'C:\Python-ML files\CodeGuard-AI\frontend'
npm run dev
```

Open **http://127.0.0.1:5173**. API docs: **http://127.0.0.1:8000/docs**. The Vite server proxies `/api` to port 8000. Load an example or paste one complete function, select its language, and click **Analyze code**. Examples are demonstration inputs; their results are computed by the model and may be uncertain or incorrect. The `examples/` directory contains five held-out Juliet functions with provenance for upload demonstrations; regenerate them with `.\.venv\Scripts\python -m scripts.export_examples` after training.

Optional history, set before starting the API:

```powershell
$env:HISTORY_ENABLED = 'true'
$env:DATABASE_URL = 'sqlite:///./history.db'
```

`.env.example` lists all settings. The Python process reads environment variables from the shell, **not automatically from `.env`**. Docker Compose reads its `.env`; Vite reads `frontend/.env` for `VITE_API_URL` at build/dev time.

## Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock
.venv/bin/python scripts/download_data.py
.venv/bin/python -m ml.prepare
.venv/bin/python -m ml.train
cd frontend && npm ci && cd ..
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
# In a second terminal: cd frontend && npm run dev
```

## Dataset preparation and evaluation

[NIST Juliet C/C++ 1.3](https://samate.nist.gov/SARD/test-suites/112) and [Java 1.3](https://samate.nist.gov/SARD/test-suites/111) provide explicitly labeled good/bad fixtures in the public domain. The downloader verifies NIST's published SHA-256 hashes. [Dataset card](docs/DATASET.md) describes exact label mappings, licensing, provenance, exclusions, and limitations.

Preparation extracts self-contained flow-01 functions, strips direct label cues, removes duplicates and invalid/conflicting examples, and joins related source/sink groups. It produces `ml/datasets/processed/samples.jsonl` and `summary.json`. No code is executed. Large archives and processed data are ignored by Git.

Training uses seed 42 and five stratified group folds: two training folds and one each for model selection, sigmoid calibration, and final testing. The actual split sizes may differ from 40/20/20/20 because groups are indivisible. Two TF-IDF classifiers are compared: balanced logistic regression (C=4) and a balanced linear SVM (C=1). Selection uses validation macro F1. The chosen frozen estimator is calibrated on a disjoint fold, then evaluated on the test fold. The test set is never used for model selection or threshold tuning.

The fixed 0.65 confidence threshold is a review policy, not a demonstrated production reliability level. Similarity below 0.12 or fewer than 40 normalized characters also triggers review. Similarity is an approximate novelty check, not a reliable out-of-distribution detector. Calibration on synthetic data does not guarantee calibration on real code.

Saved artifacts:

- `model.joblib`: complete calibrated pipeline, vectorizer, and training reference vectors.
- `metadata.json`: version, data/artifact hashes, library versions, class/language distribution, candidate validation scores, test metrics, per-language metrics, scope and limitations.
- `label_mapping.json`, `training_config.json`, `splits.json`: reproducibility and audit records.
- `confusion_matrix.png`: measured held-out confusion matrix.

The performance page displays accuracy, macro precision/recall/F1, weighted F1, per-class support/precision/recall, confusion matrix, and dataset distribution from these saved files. Macro F1 prevents the large safe class from dominating the score; per-class recall exposes missed vulnerabilities. No external-project evaluation is claimed. See [validation record](docs/VALIDATION.md) for the actual run and remaining verification limits.

## Testing

```powershell
# From repository root; prepare and train first.
.\.venv\Scripts\python -m pytest -q
Set-Location frontend
npm test
npm run build
Set-Location ..
# With backend running:
.\.venv\Scripts\python scripts\smoke_test.py
# Repeat through the frontend proxy while Vite is running:
.\.venv\Scripts\python scripts\smoke_test.py --base-url http://127.0.0.1:5173
```

Tests check dataset mapping, comment/string handling, deterministic grouped splits, model loading and five-class scores, real API inference on held-out fixtures, validation, oversized/chunked input, missing/corrupt artifacts, uncertainty, private error responses, and metadata-only history. UI tests mock HTTP to exercise asynchronous states; the live HTTP smoke test and browser check separately verify real integration. No test requires the classifier to correctly detect every example.

Example API request (PowerShell):

```powershell
$payload = @{ code = 'void copy(const char *s) { char b[16]; strcpy(b, s); }'; language = 'c' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/predict -ContentType 'application/json' -Body $payload
```

## Docker Compose

Prepare/train locally first; the model directory is mounted read-only. From the root:

```powershell
docker compose up --build
# Open http://localhost:8080
# Stop services; keep optional history:
docker compose down
```

The backend runs as an unprivileged user. Compose binds ports to localhost, waits for model readiness, and uses a named volume for optional SQLite history. The nginx frontend proxies API requests. Artifacts must match the pinned scikit-learn version. Docker startup does not download datasets or silently retrain.

Plan for 2 CPU cores, 4 GB RAM, and at least 2 GB free disk for this subset and dependencies. No GPU is needed. These are practical starting estimates, not measured capacity guarantees; load testing has not been performed.

## Troubleshooting

- **Model unavailable / 503:** Run download, preparation and training in order. Check `MODEL_DIR`. Keep `metadata.json` beside `model.joblib`; a checksum mismatch requires trusted regeneration. Restart the API after retraining.
- **NIST 403:** The downloader uses curl with a browser-compatible user agent. Retry later if NIST blocks the request. Alternatively download the linked archives manually as `ml/datasets/raw/cpp.zip` and `java.zip`; rerun the downloader to verify hashes.
- **Missing package / wheel:** Use the documented Python/Node versions and a fresh virtual environment. `npm ci` uses the checked lockfile. Windows sandbox prompts during automated setup may require filesystem/network access.
- **Frontend cannot reach API:** Confirm port 8000, `/api/health`, and the Vite proxy. If overriding `VITE_API_URL`, configure the corresponding CORS origin and restart Vite.
- **Unsupported language:** Only C/C++/Java are in this trained corpus. File extension selection is not language validation. No code parser or syntax checker is promised.
- **Uncertain or surprising result:** Expected for short or unfamiliar code. Review probabilities and the scope limitations. Do not lower the threshold merely to make a demo look better.
- **Docker unhealthy:** Ensure the artifact exists, dependency versions match, and the mounted model directory is readable. Check `docker compose logs backend`.

## Security limits and future work

Results are function-level statistical estimates. Guidance is category-level educational text, not a causal explanation of the submitted function. Exact lines and CVSS scores are deliberately absent. No dependencies, full repositories, data-flow graphs, multi-label weaknesses, or unsupported languages are analyzed. The current synthetic corpus can reward template familiarity; independent-family evaluation is the highest-priority next step.

Before broader deployment: acquire more varied and independently labeled data, especially XSS and Python/JavaScript; validate near-duplicate grouping; measure calibration and abstention on real projects; compare an optional CodeBERT model on exactly the same splits; add reliable language-aware localization, authentication, rate limits, and load testing.


## Reproducible upload examples

The `examples/` directory contains five held-out Juliet functions with source provenance. Upload them individually in the scanner. Regenerate them after training with:

```powershell
.\.venv\Scripts\python -m scripts.export_examples
```

To test real inference through the running frontend proxy:

```powershell
.\.venv\Scripts\python scripts\smoke_test.py --base-url http://127.0.0.1:5173
```

For stalled Python package transfers, the optional curl-based downloader verifies wheels against PyPI SHA-256 hashes:

```powershell
.\.venv\Scripts\python scripts\download_wheels.py
.\.venv\Scripts\python -m pip install --no-index --find-links .cache\wheels -r backend\requirements.lock
```
