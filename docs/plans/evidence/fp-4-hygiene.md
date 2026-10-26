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

## Behavior and typing (U2, U3)

The new regressions ran before corresponding fixes. Six graph cases failed: sparse class/property values contained `None`, two missing-parent formatting cases raised `AttributeError`, and two empty-definition cases raised `ValueError`. The model worker separately observed two failing alias/translation cases and eight passing serialization cases before fixing the overwrite. `fp-4/regressions.txt` retains the concise outcomes.

- Parsers omit absent text while keeping resource relationships, populated values and whitespace. Unidentified/unlabeled nodes keep their established handling, including the special OWL Thing case.
- Missing parents keep their relationship IRIs and warning, while LLM formatting omits missing lookup results.
- Empty definition corpora return `[]` with RapidFuzz installed; absent RapidFuzz still raises the existing missing-extra error.
- JSON-LD retains untagged aliases and all translations. JSON round trips and semantic XML tests cover populated and absent fields.
- Type corrections use the actual XML element type, a small prefix-trie protocol for the untyped optional extension, variadic tuples, known class indexes and both existing LLM result tuple shapes. The HTTP loader retains its `TypeError` for `None` URLs, now before opening a client.
- Fifteen fake-provider LLM tests cover list/object payloads, unknown and duplicate IRIs, defaults, ordering, limits, explanations, provider exception wrapping and parallel sets. No live LLM requests ran.
- Core-only wheels on Python 3.10.19 and 3.14.4 each passed an isolated subprocess probe, with all three optional distributions confirmed absent. The probes check local RDF, prefix and structured exact/substring queries, and fuzzy/LLM missing-extra errors. They receive no coverage credit.
- Existing test files and assertions are byte-for-byte unchanged. New test files are `tests/conftest.py`, `tests/test_parser_hygiene.py`, `tests/test_optional_search.py`, `tests/test_llm_search.py`, `tests/test_models.py` and `tests/test_core_install.py`.

## Coverage and compatibility

All runs use coverage 7.13.4, fresh data, all six `folio` modules, branch measurement and unchanged default exclusion rules. `fp-4/*-coverage.json` records counts by module as well as aggregate totals.

| Scope | Passed | Statements | Branches | Combined |
| --- | ---: | ---: | ---: | ---: |
| Original existing offline selection | 25 | 431/1177 (36.62%) | 87/572 (15.21%) | 29.62% |
| Final unchanged offline selection | 25 | 431/1189 (36.25%) | 86/576 (14.93%) | 29.29% |
| Final expanded offline selection, Python 3.12.12 | 62 | 747/1189 (62.83%) | 287/576 (49.83%) | 58.58% |
| Final expanded offline selection, Python 3.10.19 | 62 | 747/1189 (62.83%) | 287/576 (49.83%) | 58.58% |
| Final expanded offline selection, Python 3.14.4 | 62 | 747/1189 (62.83%) | 287/576 (49.83%) | 58.58% |
| Final full suite, Python 3.12.12 | 127 | 1100/1189 (92.51%) | 500/576 (86.81%) | 90.65% |

The unchanged-selection percentage change is attributable to necessary fixes, not removed tests: the new HTTP URL guard, RapidFuzz narrowing guard, empty-corpus return and parent-formatting loop add eight graph branches; consolidating JSON-LD alias accumulation removes four model branches. Known-index prefix access no longer traverses the integer branch of `__getitem__`, accounting for one fewer covered branch in the unchanged tests. Statement coverage keeps exactly 431 covered statements while the denominator increases by twelve. Coverage's existing built-in protocol exclusion recognizes four new type-only lines; no custom exclusion or suppression was added. The expanded suite exceeds both original rates substantially. `fp-4/covered-boundaries.json` lists measured executed/missing branch destinations for the parser, formatting, search and serialization boundaries.

Reproduction uses the frozen lock. Original source/input identity is recorded above. For original and final comparisons, run `pytest tests/test_iri.py tests/test_search_reconciliation.py` with `-o addopts='--cov=folio --cov-branch --cov-report=json:coverage.json --cov-report=term'`; use distinct fresh `COVERAGE_FILE` values and output filenames for each run. Expanded offline selection is `pytest tests/ --ignore=tests/test_folio.py`; full selection is `pytest tests/`. Set `FOLIO_CORE_PYTHON` to the prepared core-only interpreter for the expanded/full runs, as documented in `CONTRIBUTING.md`. Reports contain no subprocess coverage.

## Dependency audit and remediation (U4)

Auditor: isolated pip-audit 2.9.0, PyPI advisory service, Python 3.12.12 on Linux x86_64. All original/final selected-scope scans completed; findings exit 1, clean final scans exit 0. No package collection skips, automatic fixes or advisory suppressions. Machine-readable reports preserve timestamps, export SHA-256, audited inventories, unevaluated marker requirements, advisory IDs, aliases and fixes.

| Scope | Original advisories / affected packages | Final advisories / evaluated packages |
| --- | ---: | ---: |
| Core, default groups disabled | 3 / 2 | 0 / 12 |
| Core + published `search` extra, default groups disabled | 5 / 4 | 0 / 18 |
| Development group only | 4 / 2 | 0 / 57 |

Targeted compatible lock updates resolve all eight distinct advisory IDs:

| Package | Locked before → after | Dependency root/path | Advisory IDs |
| --- | --- | --- | --- |
| anyio | 4.12.1 → 4.14.2 | core httpx → anyio | PYSEC-2026-4024, PYSEC-2026-4025 |
| certifi | 2026.2.25 → 2026.10.19 | core httpx/httpcore; development Sphinx → requests | PYSEC-2026-4320 |
| h2 | 4.3.0 → 4.4.1 | search ALEA client → httpx[http2] → h2 | PYSEC-2026-3628 |
| hpack | 4.1.0 → 4.2.0 | search h2 → hpack | PYSEC-2026-4053 |
| urllib3 | 2.7.0 → 2.8.0 | development Sphinx → requests → urllib3 | PYSEC-2026-4175, PYSEC-2026-4176, PYSEC-2026-4177 |

These versions are the advisory-provided fixed versions. `uv lock --upgrade-package` targeted only those five runtime/transitive packages; the separate tooling change pins ty and updates types-lxml, removing its obsolete types-beautifulsoup4 dependency. The original library version and published runtime ranges are unchanged. Frozen installs and the runtime tests above pass after remediation.

A separate non-resolving scan of the six direct published minimum versions (pydantic 2.8.2, lxml 6.1.0, httpx 0.27.2, RapidFuzz 3.10.0, MARISA 1.2.0, ALEA 0.3.3) returned no known advisories. Its plain pinned inputs are not a hashed resolved lock and do not audit their transitive closure; `final-published-minimums-audit.json` labels that distinction.

The audit commands in `CONTRIBUTING.md` reproduce the scopes using complete hashed uv exports, `--disable-pip --require-hashes --strict`, and the same auditor. Original inputs can be reconstructed from the recorded starting commit. Advisory responses may change over time. Python/platform markers outside Linux/Python 3.12 are unevaluated, listed in each artifact; the installed-wheel compatibility checks do not constitute additional vulnerability scans. Published ranges also allow versions outside this particular lock. Consequently, the clean result applies only to the scanned inventories and advisory-feed snapshot. See [pip-audit's security model](https://github.com/pypa/pip-audit#security-model).

## Reproducible checks (U5)

`.github/workflows/hygiene.yml` adds frozen uv installs, Ruff lint/format, ty targeting Python 3.10, separate core-only wheel environments, and deterministic coverage on Python 3.10/3.14. Its 58% combined coverage floor rounds down the measured 58.58% offline result. `CONTRIBUTING.md` records the same commands and audit limitations; `CLAUDE.md` now requires zero type diagnostics and describes the prefix fallback accurately. Existing full-suite and release workflows remain unchanged.

No schema migration, data rewrite, version bump, release, outside service or frontend change. No screenshot applies. Publication, hosted checks and campaign acceptance remain with the controller.

## Final quality and delivery

- Final code review of `77a97e200992a34a101222563c4d9b476f366e68` against the starting commit returned **Ready to merge**, zero findings and complete local R1–R9/U1–U5 coverage. Seven local review lenses covered correctness, tests, project standards, maintainability, API contracts, reliability and adversarial checks. The checkout disables external cross-model review; the adversarial pass used a local reviewer. The sanitized durable result is `fp-4/review.json`.
- Simplification reviewed reuse, quality, efficiency, test value and comments. Two redundant comments were removed; all proof tests stayed intact. No actionable findings remain. The plan, tests and receipt already preserve the maintenance reasoning, so no separate learning document was needed.
- A final matching-environment check of the original source, exported from the starting commit and checked from its own root against the final development environment, exactly reproduced `fp-4/original-source-ty-chosen.txt` (46 diagnostics). Thus the five audited dependency updates did not change the diagnostic comparison; final source has zero diagnostics under the same environment.
- Workflow YAML parsed locally; trigger, Python-matrix and read-only permission fields were checked. The recorded matrix environments passed Ruff and ty, and all 62 deterministic cases passed on Python 3.10/3.14. Hosted execution is not claimed.
- Browser verification: skipped because the changed library, tests, CI and contributor documents expose no browser routes. No screenshot is required.
- Work is committed locally on `drawdown/fp-4`. No remote was added and no push, PR, merge or deployment was attempted. The controller owns publication, hosted checks and the missing campaign excerpts. There is no held change or personal decision required.
- Final `pyproject.toml` SHA-256: `2478a36f2e766e5c5e161ef22f5f1c5825b3a5f5f22280fc4396cbc2c85f4fd9`.
- Final `uv.lock` SHA-256: `d726f587ff9bf7056f4fcb4061e962ab03f426691e9842e0b33f53f19e5eea58`.
