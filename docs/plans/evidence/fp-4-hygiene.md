# fp-4 library hygiene evidence

## Starting state (U1)

- Clean `drawdown/fp-4` at `1828960305448deb24ccce25b30e4d6be0b3ef91`; no git remote. Package version remains 0.4.1.
- Original `pyproject.toml` SHA-256: `e65ddb60efbcb2871edfef7b494701cf48bc6bbbf3f05f95154bf88d9fa63b76`.
- Original `uv.lock` SHA-256: `3a207fddc2b91b31d31c69b4ef51b0fcc7eee243ac86c6c17edcca7dcdec8277`.
- Linux x86_64; Python 3.12.12; uv 0.9.22; pytest 9.1.1; pytest-cov 7.1.0; coverage 7.13.4; Ruff 0.15.6.
- `uv sync --frozen --python 3.12` succeeded. All 25 existing offline tests and all 90 original full-suite tests (including ten benchmarks and live HTTP/GitHub ontology checks) passed.
- Baseline coverage uses `--cov=folio --cov-branch` with fresh data files. Offline selection: `tests/test_iri.py tests/test_search_reconciliation.py`; full selection: `tests/`. Machine-readable totals for all six source modules are in `fp-4/original-*-coverage.json`.
- ty 0.0.92 targeting Python 3.10 produced 47 diagnostics using types-lxml 2024.12.13. With unchanged source and types-lxml 2026.2.16 it produced 46 diagnostics. Both diagnostic lists are retained. The new stubs remove one diagnostic independently of implementation. No runtime packages changed in this tooling step.
- Declared ty 0.0.92 and types-lxml 2026.2.16 in the development group; frozen sync, Ruff lint and format checks pass. The stubs cover current lxml APIs ([upstream releases](https://github.com/abelcheung/types-lxml/releases)); the actual element return annotation will still be corrected to `_Element`.
- Original core, published `search` extra, and development-only exports were saved before dependency edits. Audit reports retain input digests, evaluated package versions and advisory identifiers. Original scans completed with findings: core 3 advisories / 2 packages; search 5 / 4; development 4 / 2. Remediation and final scope limitations follow below.
- The chief campaign plan and common mandate are absent from the sandbox. The supplied campaign rules govern this run; the controller still supplies the cited Goal Capsule and R-ID excerpts for campaign acceptance. Hosted CI and publication remain controller-owned.
