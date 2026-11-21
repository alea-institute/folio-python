# Expanded-search documentation verification

Date: 2026-11-20

Plan: `docs/plans/2026-11-20-2044-docs-fp-9-expanded-search-plan.md`

Branch: `drawdown/fp-9`

## Scope

The build began on a clean worktree at `58fc421`, with the plan already committed
and no remote configured. Source review confirmed that the README and examples
still lacked query-expansion guidance. Implementation commit `e5e3d5e` adds:

- A README section explaining use cases, all public arguments and defaults,
  fallback, result fields, fusion scores, and serialization.
- `examples/expanded_search.py`, with an importable async helper and a runnable
  demo using a fixed stub LLM response.
- `tests/test_expanded_search_example.py`, exercising real search over local RDF
  while blocking HTTP requests and disabling default provider initialization.

The library, existing tests, dependency files, version, and publishing
configuration are unchanged. No live LLM is used by the new tests or demo.
The standalone demo uses normal ontology loading and may download public data.

## Verification

Environment: Linux, CPython 3.14.0, frozen dependencies from `uv.lock`.

| Check | Command or method | Result |
| --- | --- | --- |
| Baseline | `uv run --frozen pytest tests/` | 296 passed, 2 core-only installation checks skipped; 31.76 seconds |
| Test-first check | Run the new example tests before creating the example | 1 failure and 4 errors, all from the absent example file |
| Focused suite | `uv run --frozen pytest tests/test_expanded_search_example.py tests/test_expansion.py -o addopts=''` | 39 passed |
| Full suite with isolated core-only wheel | `FOLIO_CORE_PYTHON="$CORE_ENV/bin/python" uv run --frozen pytest tests/` | 303 passed, no skips; 26.31 seconds |
| Lint | `uv run --frozen ruff check --fix folio/ tests/ examples/expanded_search.py` | Passed; no fixes needed |
| Format | `uv run --frozen ruff format folio/ tests/ examples/expanded_search.py` | 23 files unchanged |
| Types | `uv run --frozen ty check folio/` | Passed with zero diagnostics |
| Standalone demo | `uv run --frozen python examples/expanded_search.py` | Returned ontology hits and expansion source `llm` from the fixed demo stub |
| Whitespace | `git diff --check` | Passed |

`CORE_ENV` denotes the separate environment prepared with
`UV_PROJECT_ENVIRONMENT="$CORE_ENV" uv sync --frozen --python 3.14 --no-default-groups --no-editable`,
following `CONTRIBUTING.md`. Both installed-wheel probes ran in the final suite.

The five new cases cover safe import, successful expansion with known fixture
IRIs and matching terms, JSON serialization, fallback with an absent provider,
fallback with a failing provider, and opting out without invoking the provider.
The successful case covers both expansion and serialization. The tests use
RapidFuzz explicitly so optional kaos installation does not change expectations.

## Review and delivery

The lfg simplification pass used five separate reviewers for reuse, quality,
efficiency, test value, and comments. It found no changes needed; proof tests
were preserved. The ce-code-review correctness pass used the lite path against
the task's starting commit, checked the plan and `CLAUDE.md`, and found no
actionable findings or missing requirements. This local review does not claim
the campaign's later Astra/Fable gate has run.

The browser-test scope contains no front-end routes, so browser testing and a
screenshot are not applicable. No browser was launched.

The chief campaign plan and common mandate file remain unavailable in this
lane. Work follows the supplied campaign rules; the controller must check the
missing authority excerpts before campaign acceptance, as the plan records.

Commits remain local for the controller to scan, push, and submit. There are no
held changes or decisions requiring Damien for this item.
