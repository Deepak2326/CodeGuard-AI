"""Exercise the live HTTP API with a held-out example from each class."""
import json
from pathlib import Path
import httpx
import argparse

ROOT = Path(__file__).resolve().parents[1]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    hashes = set(json.loads((ROOT/'ml/artifacts/splits.json').read_text())['test'])
    rows = [json.loads(line) for line in (ROOT/'ml/datasets/processed/samples.jsonl').read_text().splitlines()]
    with httpx.Client(base_url=args.base_url,timeout=30) as client:
        assert client.get('/api/health').json()['model_ready']
        for label in range(5):
            row = next(row for row in rows if row['label'] == label and row['sha256'] in hashes)
            result = client.post('/api/predict',json={'code':row['code'],'language':row['language']})
            result.raise_for_status()
            payload = result.json()
            assert len(payload['probabilities']) == 5
            print(json.dumps({'expected_class':label,'predicted':payload['predicted_category'],'confidence':payload['confidence']}))
        print('Live API smoke test passed.')

if __name__ == '__main__': main()
