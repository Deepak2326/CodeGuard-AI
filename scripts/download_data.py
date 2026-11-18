"""Download immutable Juliet 1.3 archives and verify NIST SHA-256 hashes."""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "cpp": ("2017-10-01-juliet-test-suite-for-c-cplusplus-v1-3.zip", "ada9d7e1c323d283446df3f55bdee0d00bda1fed786785fe98764d58688f38eb"),
    "java": ("2017-10-01-juliet-test-suite-for-java-v1-3.zip", "d985f4177c2bcd7b03455a05c1c8f2e755f55c9eb250accd052f05f877347e60"),
}

def download():
    dest = ROOT / "ml/datasets/raw"
    dest.mkdir(parents=True, exist_ok=True)
    for language, (filename, expected) in SOURCES.items():
        path = dest / f"{language}.zip"
        if not path.exists():
            print(f"Downloading {filename}", flush=True)
            partial = path.with_suffix(".part")
            subprocess.run(["curl", "--fail", "--location", "--retry", "3", "--max-time", "600", "--user-agent", "Mozilla/5.0", "--output", str(partial), f"https://samate.nist.gov/SARD/downloads/test-suites/{filename}"], check=True)
            with partial.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                    raise ValueError(f"Checksum mismatch: {partial}")
            partial.replace(path)
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"Checksum mismatch: {path}")
        print(f"Verified {language}: {actual}", flush=True)

if __name__ == "__main__":
    download()
