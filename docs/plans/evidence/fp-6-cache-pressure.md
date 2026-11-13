# Cache-pressure restoration verification

The fp-6 branch restores PR #24's harness and adds a fast integration regression
on the supplied current-library baseline. The replacement PR supersedes **#24
and #27**. Publication, fresh-main confirmation, campaign reviews and merging
remain with the controller and merge gate.

## Revision and scope

- Integration base: `627fa4c450392c30282baaf68fd9c9cfeda0f955`.
- Committed implementation tested: `13c97713f54d404019676300a5ad050b60d57b2c`.
- PR source head: `a9768debb9a815773b83163031418728e1666142`.
- Replayed all four source commits: `2efab9e`, `3ea4ba0`, `8834d20`, `a9768de`.
- Resolved configuration conflicts additively, preserving the shared local
  ontology fixture, branch coverage, type-check target and dependencies.
- Scoped RapidFuzz selection to the cache fixture and made the prefix parity
  test disable both instance tries, so its second search exercises Python.
- Added `test_benchmark_harness_tiny_cache_bounds` to the ordinary selection.
  Its child process joins the real benchmark plugin and pressure runner for all
  three scenarios, using real searches and 128-entry caches with a logical clock.
- Production source, package version and lockfile are unchanged. Existing
  baseline test functions are unchanged; every PR test function is retained.
  The fallback parity test retains every original assertion.

The local `main` ref is `35814e6e405c3a17d7a2240d8ea0efe7b4179461`, an ancestor
of the supplied integration base. It does not establish current upstream state.
The clone has no remote; the controller must compare the branch with fresh main.
The chief campaign plan was absent from the sandbox. Its cited excerpts could
not be read locally; the explicit build instruction and supplied standing rules
governed execution, and campaign-authority cross-checking remains external.

## Verification

Python 3.13.11, uv 0.9.22, locked dependencies. Tool versions are also recorded
in [the current measurement JSON](fp-6-cache-pressure.json).

| Check | Result |
| --- | --- |
| Baseline `uv run --frozen pytest tests/` | 195 passed, 1 skipped, 32.78 seconds. The skip required a separately installed core-only interpreter. |
| Restored harness before compatibility changes | 25 passed, 3 failed, 3 skipped. Failures reproduced KAOS bypassing the shared fuzzy cache. |
| New integration test before compatibility changes | Failed as intended: two child prefix cases passed; the fuzzy case observed no shared-cache activity. |
| Cache-pressure, KAOS and structured-query test modules after changes | 64 passed, 3 opt-in skips, 21.06 seconds. |
| Full `uv run --frozen pytest tests/` with `FOLIO_CORE_PYTHON` set | 225 passed, 3 opt-in skips, 47.18 seconds. Includes all existing benchmarks, KAOS and expansion tests, and an isolated core-only wheel probe. |
| Sustained pressure with `--run-cache-pressure --no-cov` | 3 passed, 29 deselected, 181.46 seconds. No scenario skipped. |
| `uv run --frozen ruff check --fix folio/ tests/` | Passed; no automatic changes required. |
| `uv run --frozen ruff format folio/ tests/` | All 21 files unchanged. |
| `uv run --frozen ty check folio/` | Passed, zero diagnostics. |
| Test preservation and scope | AST comparison preserved every baseline test; retained all PR tests and added one new top-level test. `git diff --check` passed. |

The core-only environment was prepared with the documented frozen, noneditable,
no-default-groups installation on Python 3.13 before setting `FOLIO_CORE_PYTHON`.
No test was weakened or skipped to accommodate the sandbox. The three final
ordinary-suite skips are exactly the sustained scenarios' existing opt-in gate.

## Sustained measurements

Measured from the clean implementation commit above using:

```bash
uv run --frozen pytest tests/test_cache_pressure.py -m cache_pressure --run-cache-pressure --no-cov --benchmark-json=<temporary-raw-report>
```

| Scenario | Measured seconds | Requests | Misses | Checkpoints | Final selected-cache entries |
| --- | ---: | ---: | ---: | ---: | ---: |
| prefix-sensitive | 60.021 | 2,441,216 | 1,258,625 | 11 | 128 |
| prefix-insensitive | 60.017 | 1,933,504 | 996,836 | 11 | 128 |
| fuzzy-mixed | 60.026 | 312,512 | 156,132 | 11 | 128 |

All reported final and checkpoint cache sizes were at most 128. Every measured
request returned its expected class; fuzzy results retained the exact score of
100. All scenarios exceeded 12,800 post-warmup misses and 10 checkpoints, ran
for at least 60 seconds and finished before the 180-second cooperative deadline.
The tiny integration regression separately checks occupancy before cleanup and
confirms tracing and the shared fuzzy cache are cleaned afterward.

The [fp-2 JSON](fp-2-cache-pressure.json) is unchanged historical evidence for
its own recorded revision `58c53690a798c7b4378ea062f80d3d2e439b88df`.
The [fp-6 JSON](fp-6-cache-pressure.json) contains only current harness reports
and public revision/tool identifiers. Raw plugin host metadata was not committed.
Memory deltas and batch timings are observations, not process-memory or latency
guarantees. These finite synthetic-ontology runs do not prove unlimited-runtime
stability. See [the reproduction guide](../../benchmarks/cache-pressure.md).

No frontend changed, so browser screenshots are not applicable. No release,
schema migration, data rewrite or outside service is part of this change.

## Local review

`ce-code-review` checked revision `f1b468178fd0df3e3e8fb1a967a6124d35c8efc8`
against the supplied integration base and explicit restoration plan. Its local
correctness and requirements review found no actionable issues. Final Ruff
lint, Ruff format-check and ty checks passed. No review fixes were needed.
This receipt covers local review; the controller still owns the campaign's
Astra/Fable reviews and fresh-main verification before publication and merge.
