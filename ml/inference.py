"""Reusable trained-model inference; no keyword-based classification fallback."""
import json
import hashlib
from pathlib import Path
import joblib
import numpy as np
from ml.preprocessing import normalize

class Predictor:
    def __init__(self, artifact_dir):
        directory = Path(artifact_dir)
        metadata = json.loads((directory / 'metadata.json').read_text())
        path = directory / 'model.joblib'
        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata['artifact_sha256']:
            raise ValueError('Model checksum mismatch')
        # Joblib is executable serialization: only load artifacts produced by trusted training.
        bundle = joblib.load(path)
        self.model = bundle['model']
        self.vectorizer = bundle['vectorizer']
        self.reference = bundle['reference_vectors']
        self.metadata = metadata
        if list(self.model.classes_) != list(range(5)):
            raise ValueError('Model must have exactly five ordered classes')

    def predict(self, code, language):
        if language not in self.metadata['supported_languages']:
            raise ValueError('Unsupported language')
        clean = normalize(code)
        probability = self.model.predict_proba([clean])[0]
        if not np.isfinite(probability).all(): raise RuntimeError('Invalid model output')
        top = int(probability.argmax())
        vector = self.vectorizer.transform([clean])
        similarity = float((vector @ self.reference.T).max())
        reasons = []
        if probability[top] < self.metadata['threshold']: reasons.append('Confidence below the review threshold.')
        if len(clean) < self.metadata['minimum_characters']: reasons.append('Too little code context for a reliable assessment.')
        if similarity < self.metadata['minimum_similarity']: reasons.append('Input differs substantially from training examples.')
        if top not in self.metadata['language_scope'][language]: reasons.append('Leading category was not evaluated for this language.')
        return dict(class_id=None if reasons else top, leading_class_id=top,
                    predicted_category='Uncertain — Manual Review Recommended' if reasons else self.metadata['categories'][top],
                    confidence=float(probability[top]), probabilities=[dict(class_id=i, category=name, probability=float(probability[i])) for i,name in enumerate(self.metadata['categories'])],
                    uncertain=bool(reasons), uncertainty_reasons=reasons, similarity=similarity,
                    model_version=self.metadata['version'])
