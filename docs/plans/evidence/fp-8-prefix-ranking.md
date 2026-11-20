# Prefix relevance verification

Build date: 2026-11-20. Scope: mandate fp-8 on `drawdown/fp-8`, from plan commit
`310194d`; implementation base `627fa4c450392c30282baaf68fd9c9cfeda0f955`.
The existing plan remains unchanged at
`docs/plans/2026-11-13-1226-feat-fp-8-prefix-relevance-plan.md`.

## Result

Both prefix paths share a documented score for each matching label occurrence.
Primary labels dominate aliases; exact matches dominate prefixes within each
group. Secondary scores prefer shorter keys and minimum known depth, penalize
exclusively low-utility branch membership, and use bounded direct location
references as an ontology prominence proxy. The initial planned weights passed
without adjustment. Ties use IRI, then class index. No example-specific boost
is present.

Parsing retains one structural-score float per class. Depth and branch walks
terminate on cycles, references are deduplicated by source and target, and
refresh rebuilds metadata. Public parsed contents and both oldest-entry
128-result caches retain their existing contracts. No signature, dependency,
version, workflow, publishing, or frontend change was made.

## Verification

The clean starting branch still used tuple ordering. `uv sync --frozen` installed
the locked default groups on Python 3.13.11. The baseline full suite passed
195 tests with the existing core-only wheel test skipped because its separate
interpreter had not yet been configured.

Before implementation, all 12 new metadata tests failed for missing metadata.
Before replacing tuple ordering, 18 ranking cases failed, including both live
California/Caldas examples and offline depth, branch, and label-provenance
cases. The remaining 12 selected characterization cases passed.

| Final check | Result |
| --- | --- |
| `uv run --frozen pytest tests/`, with `FOLIO_CORE_PYTHON` set | **254 passed**, no skips; includes live ontology and benchmarks |
| `uv run --frozen pytest tests/test_prefix_ranking.py tests/test_search_reconciliation.py -o addopts=''` | **65 passed** |
| `uv run --frozen pytest tests/test_folio.py -k prefix -o addopts=''` | **11 passed**, including unchanged Michigan expectations |
| `uv run --frozen pytest tests/test_core_install.py -o addopts=''`, with rebuilt core interpreter | **2 passed**, isolated `-I` imports outside the checkout |
| `uv run --frozen ruff check --fix folio/ tests/` | Passed, no diagnostics |
| `uv run --frozen ruff format folio/ tests/` | Passed, 21 files unchanged on final run |
| `uv run --frozen ty check folio/` | Passed, zero diagnostics, configured Python 3.10 target |
| `git diff --check` | Passed |

The Python 3.10 and 3.14 hygiene layouts were reproduced separately using
`uv sync --frozen --python <version> --no-default-groups --group dev --extra search`
for development and `--no-default-groups --no-editable --reinstall-package folio-python`
for each isolated core installation. `UV_PROJECT_ENVIRONMENT` selected separate
scratch environments, and `FOLIO_CORE_PYTHON` selected the corresponding wheel
interpreter. Python 3.10's read-only default toolchain directory required a
writable scratch `UV_PYTHON_INSTALL_DIR`; no project configuration changed.

Both layouts ran `python -m pytest tests/ --ignore=tests/test_folio.py` with
`--cov=folio --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=58`:
**177 passed, 10 existing kaos-extra skips, 69.16% combined coverage** in each.
The published search extra omits kaos; the default-group full suite above
includes it and passed those cases. Neither new wheel test skipped.

An AST comparison against `310194d` confirmed every existing test function,
fixture, helper, and test class remained identical. New tests cover the
MARISA/Python and sensitive/insensitive matrix, Unicode casefold collisions,
deterministic ties, provenance collisions, score dominance, malformed
restrictions, cycles, missing parents, mixed branches, refreshed rank inputs,
cached misses, and cache eviction.

Nine isolated in-memory mutation checks were detected by the new tests:
removing primary, exact, depth, branch, or location-reference scoring; admitting
wrong predicates or self references; counting duplicate references; and
mutating public class contents during the first metadata build. Mutation
experiments did not modify repository source. The final check was added after
review showed that a snapshot taken only after parsing could miss idempotent
corruption on the first build; the earlier assertions were preserved.

## Review and delivery boundaries

The five-persona simplification pass retained the shared scorer and bounded
metadata design, replaced temporary candidate lists with iterators, and removed
redundant private comments. All proof tests were preserved. The new first-build
preservation regression addresses the test review's concrete coverage gap.

The chief campaign plan and shared mandate file are absent from this clone;
their excerpts could not be independently read. The supplied controller mandate
and committed item plan governed this build. No remote was added or credentials
sought. Campaign Astra/Fable review, publication, and merging belong to the
controller and are not claimed by this local verification.

The implementation PR closes #17. For the separate documentation repository,
the controller can use this description in its prefix-search reference:

> Prefix search returns unique classes ranked by the best matching primary or
> alternative label. Primary matches precede aliases, and exact matches precede
> prefix matches within each group. Shorter labels, shallower depth, branch
> utility, and bounded direct location references refine the order; IRI breaks
> ties. Case-insensitive matching uses Unicode casefolding. Both case modes keep
> their existing 128-entry caches and the public signature is unchanged.
