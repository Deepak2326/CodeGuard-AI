# Validation record

Validated locally on Windows using Python 3.14.7 and Node 24.18.0. This record describes observed checks, not a production certification.

## Data and model

- Both official Juliet 1.3 archives passed NIST's published SHA-256 checks.
- 989 extracted functions; 198 duplicate instances discarded; 791 retained functions in 338 groups.
- Class counts: SQL injection 60; buffer overflow 244; XSS 18; integer overflow 90; safe 379.
- Languages: C 542; C++ 123; Java 126.
- Split sizes: train 310; validation 154; calibration 164; test 163. Integrity tests verify no group or exact hash overlap.
- Validation macro F1: logistic regression 0.84494; linear SVM 0.96232. The SVM was selected before test evaluation.
- Reproducing the training with the same data and seed produced identical candidate scores and aggregate test results. No hyperparameters were adjusted against the test scores.

| Held-out metric | Value |
|---|---:|
| Accuracy | 0.987730 |
| Macro precision | 0.992000 |
| Macro recall | 0.994872 |
| Macro F1 | 0.993321 |
| Weighted F1 | 0.987776 |
| Multiclass log loss | 0.095438 |
| Coverage at confidence ≥ 0.65 | 0.957055 |
| Accuracy among confidence-accepted examples | 0.993590 |

Coverage here refers only to the confidence threshold, not the additional inference-time context, similarity, and language-scope gates.

| Class | Test support | Precision | Recall |
|---|---:|---:|---:|
| SQL Injection | 15 | 1.0000 | 1.0000 |
| Buffer Overflow | 48 | 0.9600 | 1.0000 |
| XSS | 4 | 1.0000 | 1.0000 |
| Integer Overflow | 18 | 1.0000 | 1.0000 |
| Safe Code | 78 | 1.0000 | 0.9744 |

These high scores reflect a small, templated synthetic dataset. Four test XSS cases cannot establish general detection reliability. C++ integer overflow and safe Java XSS are not represented. No independent production-code benchmark was run. Consult `ml/artifacts/metadata.json` for exact numbers and the confusion matrix.

## Functional checks

- 24 pytest cases passed for dataset mapping, extraction, normalization, deterministic splits, saved artifact inference, default artifact path, observed language scope, API validation, malformed/oversized/chunked input, missing and corrupt models, uncertainty, metadata-only history and private errors.
- Seven React/Vitest tests passed for editor input, language selection, real request payload construction, pending/success/error states, clearing stale results, file upload and abstention. These component tests mock the API and editor.
- TypeScript checking and Vite production build passed. Monaco assets are bundled locally; unsupported language workers are excluded. The editor bundle still exceeds Vite's 500 KB chunk warning threshold.
- `npm audit` reported zero known dependency vulnerabilities after dependency updates.
- `pip check` reported no broken requirements.
- The live frontend returned HTTP 200. A held-out example from each of the five classes passed the live HTTP smoke test both directly at port 8000 and through the Vite frontend proxy at port 5173. Predictions and scores matched across the two routes.
- Missing-model behavior was tested without any fallback predictions. History was tested with a temporary SQLite database.

The installed Starlette test client emits a deprecation warning for httpx; tests pass. The calibration wrapper emits a small-class warning because its internal cross-validation splitter sees only four XSS calibration examples. Its wrapped base estimator is frozen, so no base-model fitting occurs on calibration data. Small calibration support remains a statistical limitation.

## Verification limits

- Browser visual and click-through QA could not finish: the in-app browser access host was unavailable, and native Chrome windows were minimized with no working restore exposed by the available UI tool. HTTP integration and component tests passed, but these do not replace visual QA.
- `docker` was not available on PATH. Dockerfiles, nginx configuration and Compose are supplied, but a container build/startup has not been verified here.
- CodeBERT fine-tuning is optional and was not implemented. No transformer accuracy or GPU support is claimed.
- No authentication, public deployment, load testing, or real-project security-detection validation was performed. The app is intended for localhost academic demonstration.
