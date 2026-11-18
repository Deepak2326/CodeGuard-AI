# Dataset card

## Sources and licensing

| Source | Origin | Use | License |
|---|---|---|---|
| [Juliet C/C++ 1.3](https://samate.nist.gov/SARD/test-suites/112) | NSA Center for Assured Software, distributed by NIST | CWE-121, CWE-122, CWE-190 baseline functions | US public domain; CC0 1.0 for claimed foreign rights, per NIST |
| [Juliet Java 1.3](https://samate.nist.gov/SARD/test-suites/111) | Same | CWE-89 and CWE-80 baseline functions | Same |

The downloader uses the exact archive names and published SHA-256 hashes in `scripts/download_data.py`. No credentials or paid services are required. curl must be installed. Archives are read directly, never compiled or executed. They are ignored by Git.

## Mapping

| ID | Category | Actual source annotations |
|---|---|---|
| 0 | SQL Injection | CWE-89 bad functions |
| 1 | Buffer Overflow | CWE-121 and CWE-122 bad functions |
| 2 | Cross-Site Scripting | CWE-80 bad functions |
| 3 | Integer Overflow | CWE-190 bad functions |
| 4 | Safe Code | Explicit Juliet good functions for the above target weaknesses |

[MITRE defines CWE-80 as a child of CWE-79](https://cwe.mitre.org/data/definitions/80.html). Its HTML/script neutralization failures align with the XSS target. CWE-120 is related to the memory category but is not included in this extraction. Do not infer broader coverage from category names.

## Extraction and integrity

Only `*_01.c`, `*_01.cpp`, and `*_01.java` flow-01 baseline files are selected. A string-aware brace scanner extracts void good/bad functions. Good dispatchers that merely call helper functions are excluded. Other flow variants and interprocedural helper files are deliberately excluded; flattening them could produce incomplete or incorrect labels.

Comments, CWE/function label identifiers, and function access/storage modifiers are normalized to remove direct label leakage. Whitespace is normalized. Strings are retained so SQL/HTML operators remain available. Samples with invalid decoding or insufficient content are rejected. SHA-256 identifies exact normalized duplicates. Related filename source/sink families share groups across memory CWEs. Java examples are grouped by input-source family across SQL operations and XSS variants. Exact duplicate functions shared across groups are discarded entirely; duplicates within one group retain one representative. Conflicting labels are removed, never arbitrarily resolved.

The processed JSONL records retain archive-relative source path, original function name, CWE, language, normalized content, group, label, and hash. `summary.json` reports exclusions, distribution, and groups. These provenance fields are never model features.

## Known limitations

This corpus is synthetic and highly templated, not a representative sample of production vulnerabilities. Normalization and grouping reduce leakage but cannot remove all shared-template similarity. Grouped evaluation does not substitute for an independent-project benchmark.

Safe labels mean the *target weakness* is absent in the Juliet fixture. They do not establish that a function is secure in all contexts. All examples are single-label. The current subset has very few XSS examples. Per-class support and recall must accompany aggregate metrics.

Language is confounded with vulnerability family: Java supplies SQL/XSS, C supplies memory/integer issues, and C++ supplies memory issues only. After removing shared duplicate fixtures, this subset has no safe Java XSS counterparts; its Java safe examples are SQL fixtures. The model can still learn language cues. Unsupported class/language combinations trigger abstention when they lead the scores. No Python or JavaScript support is claimed. Adding those languages requires separately licensed, explicitly labeled paired examples, provenance, grouped splits, and evaluation.

Potential next datasets must be reviewed for licensing and label reliability before import. This release does not silently treat unannotated code as safe, fabricate examples, or claim an independent-family evaluation.

