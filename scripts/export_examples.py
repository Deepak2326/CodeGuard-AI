"""Export one held-out Juliet function per class for reproducible upload demos."""
import json
from pathlib import Path
from zipfile import ZipFile
from ml.prepare import functions
from ml.preprocessing import IDENTIFIER

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['sql_injection', 'buffer_overflow', 'xss', 'integer_overflow', 'safe_code']

def main():
    hashes = set(json.loads((ROOT/'ml/artifacts/splits.json').read_text())['test'])
    rows = [json.loads(line) for line in (ROOT/'ml/datasets/processed/samples.jsonl').read_text().splitlines()]
    destination = ROOT/'examples'
    destination.mkdir(exist_ok=True)
    manifest = []
    for label, name in enumerate(NAMES):
        row = next(row for row in rows if row['label'] == label and row['sha256'] in hashes)
        archive_name = 'java' if row['language'] == 'java' else 'cpp'
        with ZipFile(ROOT/f'ml/datasets/raw/{archive_name}.zip') as archive:
            code = next(code for function,code in functions(archive.read(row['source']).decode()) if function == row['function'])
        code = IDENTIFIER.sub('example', code)
        code = '\n'.join(line.rstrip() for line in code.splitlines() if line.strip())
        filename = name + {'c':'.c','cpp':'.cpp','java':'.java'}[row['language']]
        (destination/filename).write_text('// Held-out Juliet demonstration function; not a complete standalone program.\n' + code + '\n',encoding='utf-8')
        manifest.append(dict(file=filename, expected_label=label, source=row['source'], function=row['function'], split='test', license='NIST public domain / CC0', sha256=row['sha256']))
    (destination/'provenance.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Exported five held-out demonstration functions to examples/.')

if __name__ == '__main__': main()
