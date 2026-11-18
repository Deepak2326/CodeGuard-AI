"""Create/upload the Docker Space using a token supplied on stdin only."""
import getpass
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]

def main():
    token = getpass.getpass('Hugging Face token (input hidden): ')
    api = HfApi(token=token)
    user = api.whoami()
    username = user['name'] if isinstance(user, dict) else user.name
    repo_id = f'{username}/codeguard-ai'
    api.create_repo(repo_id=repo_id, repo_type='space', space_sdk='docker', private=False, exist_ok=True)
    files = [
        'Dockerfile.huggingface', 'hf_space_README.md', 'backend/__init__.py', 'backend/requirements.lock',
        'backend/app/__init__.py', 'backend/app/categories.py', 'backend/app/history.py', 'backend/app/main.py',
        'ml/__init__.py', 'ml/inference.py', 'ml/preprocessing.py',
        'ml/artifacts/model.joblib', 'ml/artifacts/metadata.json', 'ml/artifacts/label_mapping.json',
        'ml/artifacts/training_config.json', 'ml/artifacts/confusion_matrix.png', 'frontend/dist/index.html',
    ]
    # Include all Vite assets, while excluding local source and node_modules.
    asset_root = ROOT / 'frontend' / 'dist'
    for path in asset_root.rglob('*'):
        if path.is_file(): files.append(str(path.relative_to(ROOT)).replace('\\','/'))
    for rel in files:
        path = ROOT / rel
        if path.exists():
            target = rel.replace('Dockerfile.huggingface','Dockerfile').replace('hf_space_README.md','README.md')
            api.upload_file(path_or_fileobj=str(path), path_in_repo=target, repo_id=repo_id, repo_type='space', commit_message='Deploy CodeGuard AI')
    print(f'https://huggingface.co/spaces/{repo_id}')
    print(f'https://{username}-codeguard-ai.hf.space')

if __name__ == '__main__': main()
