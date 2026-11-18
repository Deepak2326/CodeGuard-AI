"""Train/select on train+selection sets, calibrate separately, evaluate test once."""
import hashlib
import json
import platform
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix, log_loss
from ml.preprocessing import normalize

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["SQL Injection", "Buffer Overflow", "Cross-Site Scripting", "Integer Overflow", "Safe Code"]
SEED = 42

def split_data(frame):
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    folds = [test for _, test in splitter.split(frame.code, frame.label, frame.group)]
    parts = {"test": folds[0], "calibration": folds[1], "validation": folds[2], "train": np.concatenate(folds[3:])}
    for name, idx in parts.items():
        if set(frame.iloc[idx].label) != set(range(5)): raise ValueError(f"Missing class in {name}; inspect grouping")
    for a, ia in parts.items():
        for b, ib in parts.items():
            if a != b:
                assert not set(frame.iloc[ia].group) & set(frame.iloc[ib].group)
                assert not set(frame.iloc[ia].sha256) & set(frame.iloc[ib].sha256)
    return parts

def metrics(y, pred):
    precision, recall, f1, _ = precision_recall_fscore_support(y, pred, average="macro", zero_division=0)
    return dict(accuracy=accuracy_score(y, pred), macro_precision=precision, macro_recall=recall, macro_f1=f1,
                weighted_f1=precision_recall_fscore_support(y, pred, average="weighted", zero_division=0)[2],
                classification_report=classification_report(y, pred, labels=list(range(5)), target_names=LABELS, output_dict=True, zero_division=0),
                confusion_matrix=confusion_matrix(y, pred, labels=list(range(5))).tolist())

def train():
    data_path = ROOT / "ml/datasets/processed/samples.jsonl"
    frame = pd.read_json(data_path, lines=True)
    parts = split_data(frame)
    subset = {name: frame.iloc[idx] for name, idx in parts.items()}
    candidates, scores = {}, {}
    for name, classifier in [("logistic_regression", LogisticRegression(C=4, class_weight="balanced", max_iter=2000, random_state=SEED)),
                              ("linear_svm", LinearSVC(C=1, class_weight="balanced", random_state=SEED))]:
        pipeline = Pipeline([("tfidf", TfidfVectorizer(preprocessor=normalize, analyzer="char", ngram_range=(3, 5), min_df=2, max_features=40000, sublinear_tf=True)), ("classifier", classifier)])
        pipeline.fit(subset['train'].code, subset['train'].label)
        scores[name] = metrics(subset['validation'].label, pipeline.predict(subset['validation'].code))['macro_f1']
        candidates[name] = pipeline
    selected = max(scores, key=scores.get)
    model = CalibratedClassifierCV(FrozenEstimator(candidates[selected]), method="sigmoid")
    model.fit(subset['calibration'].code, subset['calibration'].label)
    test = subset['test']
    probabilities = model.predict_proba(test.code)
    predicted = probabilities.argmax(axis=1)
    result = metrics(test.label, predicted)
    result['log_loss'] = log_loss(test.label, probabilities)
    threshold = 0.65  # Declared policy, not optimized against test outcomes.
    accepted = probabilities.max(axis=1) >= threshold
    result['confidence_coverage'] = float(accepted.mean())
    result['confidence_accepted_accuracy'] = float(accuracy_score(test.label[accepted], predicted[accepted])) if accepted.any() else None
    result['per_language'] = {lang: metrics(test.loc[test.language == lang, 'label'], predicted[test.language == lang]) for lang in sorted(test.language.unique())}
    out = ROOT / "ml/artifacts"
    out.mkdir(parents=True, exist_ok=True)
    data_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
    metadata = dict(name=f"TF-IDF + {selected} (sigmoid calibrated)", version=f"1.0-{data_hash[:10]}",
                    supported_languages=sorted(frame.language.unique()), categories=LABELS,
                    language_scope={language: sorted(int(label) for label in frame.loc[frame.language == language, 'label'].unique()) for language in sorted(frame.language.unique())},
                    dataset=json.loads((data_path.parent / 'summary.json').read_text()),
                    evaluation=result, validation_macro_f1=scores, selected=selected,
                    threshold=threshold, minimum_similarity=0.12, minimum_characters=40,
                    dataset_sha256=data_hash, seed=SEED, python=platform.python_version(), sklearn=sklearn.__version__,
                    split_sizes={k: len(v) for k, v in parts.items()},
                    limitations=["Synthetic Juliet baseline functions; no independent real-project evaluation.",
                                 "Only four vulnerable XSS examples occur in the test split; this is insufficient to establish detection reliability.",
                                 "This subset has no C++ integer-overflow examples or Java safe XSS counterparts after cross-group deduplication.",
                                 "Single-label classifier: cannot enumerate multiple vulnerabilities.",
                                 "Safe means Juliet's target weakness is absent, not proof of security.",
                                 "Language and vulnerability class are confounded in this corpus.",
                                 "Confidence is calibrated on synthetic data; it does not guarantee correctness on unfamiliar code."])
    vectorizer = candidates[selected].named_steps['tfidf']
    bundle = dict(model=model, metadata=metadata, reference_vectors=vectorizer.transform(subset['train'].code), vectorizer=vectorizer)
    joblib.dump(bundle, out / "model.joblib", compress=3)
    metadata['artifact_sha256'] = hashlib.sha256((out / 'model.joblib').read_bytes()).hexdigest()
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (out / "label_mapping.json").write_text(json.dumps(dict(enumerate(LABELS)), indent=2))
    (out / "splits.json").write_text(json.dumps({k: frame.iloc[v].sha256.tolist() for k,v in parts.items()}, indent=2))
    (out / "training_config.json").write_text(json.dumps(dict(seed=SEED, folds=5, ngram_range=[3,5], max_features=40000, min_df=2, calibration="sigmoid", threshold=threshold, selection="validation macro F1", train_folds=2), indent=2))
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    fig, ax = plt.subplots(figsize=(9,7))
    sns.heatmap(result['confusion_matrix'], annot=True, fmt='d', xticklabels=LABELS, yticklabels=LABELS, ax=ax, cmap='Blues')
    ax.set(xlabel="Predicted", ylabel="Actual", title="Juliet grouped held-out test set")
    fig.tight_layout()
    fig.savefig(out / "confusion_matrix.png", dpi=150)
    print(json.dumps({"selected": selected, "validation": scores, "test_macro_f1": result['macro_f1'], "splits": metadata['split_sizes']}, indent=2))

if __name__ == "__main__": train()
