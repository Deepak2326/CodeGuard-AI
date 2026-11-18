"""Optional curl-based wheel download for environments with slow pip HTTP transfers.

Uses PyPI release metadata, platform-compatible wheels and SHA-256 verification.
Run with a Python interpreter that has `packaging` installed, matching the target venv.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
try:
    from packaging.tags import sys_tags
    from packaging.utils import parse_wheel_filename
except ImportError:
    from pip._vendor.packaging.tags import sys_tags
    from pip._vendor.packaging.utils import parse_wheel_filename

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.cache/wheels'
TAGS = set(sys_tags())

def fetch(requirement):
    name,version = requirement.split('==')
    raw = subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--retry','2','--max-time','60','--user-agent','Mozilla/5.0',f'https://pypi.org/pypi/{name}/{version}/json'])
    metadata = json.loads(raw)
    wheels = [item for item in metadata['urls'] if item['filename'].endswith('.whl') and parse_wheel_filename(item['filename'])[3] & TAGS]
    if not wheels: raise RuntimeError(f'No compatible wheel for {requirement}')
    wheel = sorted(wheels,key=lambda w:w['filename'])[0]
    target = DEST / wheel['filename']
    valid = False
    if target.exists():
        with target.open('rb') as stream:
            valid = hashlib.file_digest(stream,'sha256').hexdigest() == wheel['digests']['sha256']
    if not valid:
        partial = target.with_suffix('.part')
        subprocess.run(['curl','--http1.1','--fail','--silent','--show-error','--location','--retry','2','--connect-timeout','15','--speed-limit','1024','--speed-time','30','--max-time','180','--user-agent','Mozilla/5.0','--output',str(partial),wheel['url']+'?download=1'],check=True)
        with partial.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest() != wheel['digests']['sha256']:
                raise ValueError(f'Checksum mismatch for {name}')
        partial.replace(target)
    with target.open('rb') as stream:
        digest = hashlib.file_digest(stream,'sha256').hexdigest()
    if digest != wheel['digests']['sha256']: raise ValueError(f'Checksum mismatch for {name}')
    print(f'Verified {requirement}',flush=True)

if __name__ == '__main__':
    DEST.mkdir(parents=True,exist_ok=True)
    requirements = [line.strip() for line in (ROOT/'backend/requirements.lock').read_text().splitlines() if line.strip() and not line.strip().startswith('#')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch,requirements))
