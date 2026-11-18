"""Extract only Juliet flow-01 self-contained good/bad functions, with provenance."""
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
from collections import Counter, defaultdict
from ml.preprocessing import normalize, strip_comments

ROOT = Path(__file__).resolve().parents[1]
MAPPING = {89: 0, 121: 1, 122: 1, 80: 2, 190: 3}
FUNCTION = re.compile(r'(?:(?:public|private|protected|static)\s+)*void\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w., ]+)?\s*\{')
LEX = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]')

def functions(source):
    source = strip_comments(source)
    for match in FUNCTION.finditer(source):
        name = match[1]
        if not re.search(r'(?:^|_)(?:bad|good(?:(?:G2B|B2G)\d*)?)$', name):
            continue
        depth = 1
        for token in LEX.finditer(source, match.end()):
            if token[0] == "{": depth += 1
            elif token[0] == "}": depth -= 1
            if depth == 0:
                body = source[match.end():token.start()]
                if re.fullmatch(r'(?:\s*good\w*\([^;]*\);\s*)+', body):
                    break  # Dispatcher, not a labeled standalone function.
                yield name, source[match.start():token.end()]
                break

def prepare():
    rows = []
    for archive_name in ("cpp", "java"):
        with ZipFile(ROOT / f"ml/datasets/raw/{archive_name}.zip") as archive:
            for name in sorted(archive.namelist()):
                path = Path(name)
                if not re.search(r'_01\.(?:c|cpp|java)$', name): continue
                match = re.match(r'CWE(\d+)_', path.name)
                if not match or int(match[1]) not in MAPPING: continue
                cwe = int(match[1])
                if archive_name == "cpp" and cwe not in (121, 122, 190): continue
                if archive_name == "java" and cwe not in (89, 80): continue
                language = {".c": "c", ".cpp": "cpp", ".java": "java"}[path.suffix]
                # Related memory classes and C/C++ source/sink templates share a group.
                family = re.sub(r'_01$', '', path.stem.split('__')[-1])
                if archive_name == 'java':
                    # Hold out input-source families across SQL operations and XSS variants.
                    source_family = re.sub(r'^CWE\d+_', '', family)
                    source_family = re.sub(r'^Servlet_', '', source_family)
                    family = source_family.split('_')[0]
                for function_name, code in functions(archive.read(name).decode("utf-8", errors="replace")):
                    clean = normalize(code)
                    if len(clean) < 50 or "\ufffd" in clean: continue
                    label = MAPPING[cwe] if re.search(r'(?:^|_)bad$', function_name) else 4
                    rows.append(dict(code=clean, label=label, language=language, cwe=cwe,
                                     source=name, function=function_name, group=f"{archive_name}:{family}",
                                     sha256=hashlib.sha256(clean.encode()).hexdigest()))
    if not rows: raise ValueError("No valid functions found")
    # Discard shared duplicate functions completely: a constant safe fixture can
    # otherwise connect every source family and make held-out evaluation impossible.
    by_hash = defaultdict(list)
    for row in rows: by_hash[row['sha256']].append(row)
    cleaned, conflicts = [], 0
    for duplicates in by_hash.values():
        first = duplicates[0]
        if len({r['label'] for r in duplicates}) > 1:
            conflicts += len(duplicates)
            continue
        if len({r['group'] for r in duplicates}) > 1:
            continue
        cleaned.append(first)
    assert set(r['label'] for r in cleaned) == set(range(5))
    dest = ROOT / "ml/datasets/processed"
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "samples.jsonl").open("w", encoding="utf-8") as output:
        for row in cleaned: output.write(json.dumps(row) + "\n")
    summary = dict(source="NIST Juliet 1.3; baseline flow 01 only", extracted=len(rows), samples=len(cleaned),
                   duplicates_removed=len(rows)-len(cleaned)-conflicts, conflicting_samples_removed=conflicts,
                   groups=len({r['group'] for r in cleaned}),
                   class_distribution=dict(Counter(r['label'] for r in cleaned)),
                   languages=dict(Counter(r['language'] for r in cleaned)))
    (dest / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

if __name__ == "__main__": prepare()
