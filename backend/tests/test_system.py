import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app
from ml.inference import Predictor
from ml.preprocessing import normalize
from ml.prepare import functions, MAPPING
from ml.train import split_data, LABELS

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / 'ml/artifacts'

@pytest.fixture(scope='module')
def client():
    with TestClient(create_app(ARTIFACTS, history_enabled=False)) as c: yield c

@pytest.fixture(scope='module')
def data():
    return pd.read_json(ROOT / 'ml/datasets/processed/samples.jsonl', lines=True)

def test_dataset_and_mapping(data):
    assert len(data) > 500
    assert set(data.label) == set(range(5))
    assert data.sha256.is_unique
    assert data.code.str.len().min() >= 50
    assert MAPPING == {89:0,121:1,122:1,80:2,190:3}
    assert len(LABELS) == 5
    assert all(data[data.label == 4].function.str.contains('good'))

def test_split_integrity_and_reproducibility(data):
    parts = split_data(data)
    second = split_data(data)
    recorded = json.loads((ARTIFACTS/'splits.json').read_text())
    for name, indexes in parts.items():
        np.testing.assert_array_equal(indexes, second[name])
        assert data.iloc[indexes].sha256.tolist() == recorded[name]

def test_preprocessing_preserves_strings_and_removes_label_cues():
    code = 'public void bad() { /* flaw */ String url="https://example.test/{x}"; }'
    result = normalize(code)
    assert 'https://example.test/{x}' in result
    assert 'flaw' not in result and 'bad' not in result and 'public' not in result
    assert normalize(result) == result
    assert normalize('static void goodG2B() { x(); }') == normalize('void bad() { x(); }')

def test_extraction_braces_in_strings_and_dispatchers():
    source = 'void bad(){char *s="}"; unsafe();} void good(){goodG2B();} void goodG2B(){safe();}'
    result = list(functions(source))
    assert [name for name,_ in result] == ['bad','goodG2B']
    assert 'unsafe();}' in result[0][1]

def test_artifact_and_probability_shape(data):
    predictor = Predictor(ARTIFACTS)
    samples = data.groupby('label').first()
    probability = predictor.model.predict_proba(samples.code)
    assert probability.shape == (5,5)
    assert np.isfinite(probability).all()
    assert ((probability >= 0) & (probability <= 1)).all()
    np.testing.assert_allclose(probability.sum(axis=1), 1)
    np.testing.assert_allclose(probability, predictor.model.predict_proba(samples.code))

def test_health_and_info(client):
    assert client.get('/api/health').json()['model_ready']
    info = client.get('/api/model-info').json()
    assert info['supported_languages'] == ['c','cpp','java']
    assert 0 <= info['evaluation']['macro_f1'] <= 1
    assert len(client.get('/api/categories').json()) == 5

def test_default_model_directory(monkeypatch):
    monkeypatch.delenv('MODEL_DIR', raising=False)
    with TestClient(create_app(history_enabled=False)) as client:
        assert client.get('/api/health').json()['model_ready']

def test_language_scope_is_observed_data(data):
    predictor = Predictor(ARTIFACTS)
    for language in predictor.metadata['supported_languages']:
        assert predictor.metadata['language_scope'][language] == sorted(data[data.language == language].label.unique())

def test_heldout_inference_through_api(client, data):
    test_hashes = json.loads((ARTIFACTS/'splits.json').read_text())['test']
    test = data[data.sha256.isin(test_hashes)]
    for label in range(5):
        row = test[test.label == label].iloc[0]
        response = client.post('/api/predict', json={'code': row.code, 'language': row.language})
        assert response.status_code == 200
        result = response.json()
        assert len(result['probabilities']) == 5
        assert result['highlighted_lines'] == []
        assert 0 <= result['confidence'] <= 1
        assert result['class_id'] in [None,0,1,2,3,4]
        assert result['history_id'] is None
        # Functional inference test, not a claim of perfect class accuracy.
        assert result['model_version']

@pytest.mark.parametrize('payload', [
    {'code':'','language':'c'}, {'code':'   ','language':'c'},
    {'code':'a'*20001,'language':'c'}, {'code':'x\0y','language':'c'},
    {'code':'print(1)','language':'python'}, {'language':'java'},
    {'code':123,'language':'c'}, {'code':'x','language':'c','extra':True},
])
def test_validation(client,payload):
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 422
    if len(str(payload.get('code',''))) > 100: assert 'a'*100 not in response.text

def test_large_and_malformed_request(client):
    assert client.post('/api/predict', content=b'x'*100001).status_code == 413
    assert client.post('/api/predict', content='{', headers={'content-type':'application/json'}).status_code == 422
    def chunks():
        yield b'x'*50001
        yield b'x'*50001
    assert client.post('/api/predict', content=chunks()).status_code == 413

def test_uncertainty(client):
    result = client.post('/api/predict',json={'code':'hello','language':'c'}).json()
    assert result['uncertain']
    assert result['class_id'] is None
    assert result['uncertainty_reasons']

def test_missing_model(tmp_path):
    with TestClient(create_app(tmp_path,history_enabled=False)) as client:
        assert not client.get('/api/health').json()['model_ready']
        assert client.get('/api/model-info').status_code == 503
        assert client.post('/api/predict',json={'code':'void f() {}','language':'c'}).status_code == 503

def test_tampered_artifact(tmp_path):
    (tmp_path/'metadata.json').write_text((ARTIFACTS/'metadata.json').read_text())
    (tmp_path/'model.joblib').write_bytes(b'not trusted')
    with pytest.raises(ValueError,match='checksum'): Predictor(tmp_path)

def test_history_opt_in_and_delete(tmp_path):
    url = 'sqlite:///' + str(tmp_path/'history.db')
    with TestClient(create_app(ARTIFACTS,history_enabled=True,database_url=url)) as client:
        source = 'void my_secret_name() { int a = 123; printIntLine(a); }'
        result = client.post('/api/predict',json={'code':source,'language':'c'}).json()
        history = client.get('/api/history').json()
        assert history['enabled'] and len(history['scans']) == 1
        assert history['summary']['total'] == 1
        assert 'my_secret_name' not in json.dumps(history)
        assert client.delete(f"/api/history/{result['history_id']}").status_code == 204
        assert client.get('/api/history').json()['summary']['total'] == 0
        assert client.delete(f"/api/history/{result['history_id']}").status_code == 404
    assert b'my_secret_name' not in (tmp_path/'history.db').read_bytes()

def test_disabled_history(client):
    assert client.get('/api/history').json() == {'enabled':False,'scans':[],'summary':None}
    assert client.delete('/api/history/1').status_code == 404

def test_internal_error_does_not_leak(data):
    with TestClient(create_app(ARTIFACTS,history_enabled=False),raise_server_exceptions=False) as client:
        def broken(*args): raise RuntimeError('sensitive-internal-details')
        client.app.state.predictor.predict = broken
        result = client.post('/api/predict',json={'code':'void example(){}','language':'c'})
        assert result.status_code == 500
        assert 'sensitive' not in result.text
