# Cache-pressure CI import repair

Verified on 2026-11-13. The replacement PR supersedes **#31 and #24**.

## Source and scope

- Supplied library baseline: `627fa4c450392c30282baaf68fd9c9cfeda0f955`
  (v0.4.2); plan-stage HEAD: `cbbdb6c`.
- Required PR #31 head: `68f84b65198e38a4ec298c2f026c8153cf66e33f`.
  All eight commits after its merge base with the lane replayed without conflicts.
- Restored pre-fix revision: `5de877a`.
- Repaired source: `81087e1985c8bec778d0354f537ab5f35a4b2261`.
  The focused checks and development full suite tested the identical source
  before its commit; the CI full suite ran after that commit. Subsequent changes
  are documentation only.
- The branch contains the harness, tests, opt-in configuration, documentation,
  and original measurement records. Historical fp-2/fp-6 measurements were not
  rewritten or presented as new measurements.
- Production files, package version, dependencies, `uv.lock`, and the CI workflow
  are unchanged from the supplied library baseline. All restored function names
  and assertion ASTs were compared against PR #31 and remain intact.

## Failure and repair

The workflow builds a distribution, then uses `poetry install --no-root` and
`PYTHONPATH=. poetry run pytest tests/`. It does not install the wheel for testing.
Pytester's subprocesses start in temporary directories; the inherited relative
path no longer identifies the checkout. At the restored revision, the focused
suite passed in the editable development environment but failed eight cases in
the fresh CI environment with `ModuleNotFoundError: No module named 'folio'`.

`prepend_checkout_pythonpath` now prepends the absolute checkout root derived
from the resolved test-module location. It preserves inherited paths, uses the
platform separator, and restores the environment through pytest's monkeypatch.
All three subprocess caller families use it, including the copied-conftest
collection path. Subprocess coverage isolation and instrumentation rejection
assertions remain unchanged.

`test_pytester_subprocess_imports_checkout` covers absent, relative, and additional
inherited paths. The child verifies the imported package's source location and
imports a module from the additional path; the parent verifies restoration.
An external, temporary pytest plugin replaced only the helper with a no-op:
all three regression cases then failed at child collection with the missing
`folio` import. That probe changed no repository file.

## Environments

| Component | Development | Fresh no-root CI layout |
| --- | --- | --- |
| Python | 3.13.11 | 3.14.4 |
| Dependency installer | uv 0.9.22, frozen lock | Poetry 2.5.1, fresh resolution |
| pytest | 9.1.1 | 9.2.0 |
| pytest-benchmark | 5.2.3 | 5.3.1 |
| pytest-cov | 7.1.0 | 7.1.0 |
| coverage | 7.13.4 | 7.17.3 |
| pytest-asyncio | 1.4.0 | 1.5.0 |
| marisa-trie | 1.4.0 | 1.4.1 |
| rapidfuzz | 3.14.3 | 3.14.6 |

The CI environment was created empty and used for both the failing and passing
runs. Poetry itself lived in a separate tools environment. Before and after the
suite, isolated Python (`-I`) reported no `folio` import spec and distribution
metadata reported no `folio-python` installation. The development editable
installation could not mask the CI result. Installed pytester source in both
environments confirms that child `PYTHONPATH` is built from the current directory
and inherited environment, rather than the parent's `sys.path`.

Separate core-only wheel environments were prepared with the matching Python
versions and `uv sync --frozen --no-default-groups --no-editable`. Both full-suite
runs set `FOLIO_CORE_PYTHON`, so the existing isolated installation test passed.

The tracked uv lock SHA-256 is
`52f79ce067b300b940e32b722bc10097e25a8341536d3e35a5a38b5e628875a6`.
Poetry generated an untracked lock with SHA-256
`b201d31f37f016af6d41cdf3437ce715c1e9edb2cc1d350722f0bf8fbb8aa04a`;
it was retained with temporary verification artifacts outside the checkout,
not introduced as a project dependency change.

## Commands and results

Commands below normalize temporary filesystem locations to `$POETRY_TOOL`,
`$CI_VENV`, `$CORE_313`, `$CORE_314`, and `$PROBE_DIR`. The Poetry invocations
used `VIRTUAL_ENV="$CI_VENV" PATH="$CI_VENV/bin:$PATH"` and the separate Poetry
executable (`$POETRY_TOOL`). Commands ran from the repository root. The workflow's
build, install, and test arguments were retained.

| Check | Command | Exit | Result |
| --- | --- | --- | --- |
| Restore | `git cherry-pick $(git merge-base HEAD 68f84b65198e38a4ec298c2f026c8153cf66e33f)..68f84b65198e38a4ec298c2f026c8153cf66e33f` | 0 | Eight commits; no conflicts |
| Development pre-fix | `uv run --frozen pytest tests/test_cache_pressure.py` | 0 | 29 passed, 3 skipped |
| CI distribution build | `$POETRY_TOOL build` | 0 | sdist and wheel built; no publication or root installation |
| CI dependency install | `$POETRY_TOOL install --no-root` | 0 | Fresh dependencies installed |
| CI pre-fix | `PYTHONPATH=. $POETRY_TOOL run pytest tests/test_cache_pressure.py` | 1 | 8 failed, 21 passed, 3 skipped; child import errors |
| CI repaired focused | `PYTHONPATH=. $POETRY_TOOL run pytest tests/test_cache_pressure.py` | 0 | 32 passed, 3 skipped |
| Development repaired focused | `uv run --frozen pytest tests/test_cache_pressure.py` | 0 | 32 passed, 3 skipped |
| Development full suite | `FOLIO_CORE_PYTHON="$CORE_313/bin/python" uv run --frozen pytest tests/` | 0 | 228 passed, 3 skipped |
| CI full suite | `PYTHONPATH=. FOLIO_CORE_PYTHON="$CORE_314/bin/python" $POETRY_TOOL run pytest tests/` | 0 | 228 passed, 3 skipped |
| Regression sensitivity probe | `PYTHONPATH=".:$PROBE_DIR" $POETRY_TOOL run pytest tests/test_cache_pressure.py::test_pytester_subprocess_imports_checkout -p no_import_fix --no-cov` | 1 | Expected: 3 failed with child import errors when the helper is disabled |
| Required lint/autofix | `uv run --frozen ruff check --fix folio/ tests/` | 0 | No changes needed |
| Required format | `uv run --frozen ruff format folio/ tests/` | 0 | 21 files unchanged |
| Final lint | `uv run --frozen ruff check folio/ tests/` | 0 | Passed, Ruff 0.15.6 |
| Final format check | `uv run --frozen ruff format --check folio/ tests/` | 0 | Passed |
| Types | `uv run --frozen ty check folio/` | 0 | Zero diagnostics, ty 0.0.92 |
| Patch whitespace | `git diff --check` | 0 | Passed |

The three skips in each full run are the existing opt-in sustained benchmarks.
No tests were deleted, newly skipped, or weakened. Live ontology integration,
ordinary benchmarks, the tiny harness's three cache scenarios, plugin rejection
cases, and the core-only wheel check all passed. This import-only repair does not
change pressure budgets, measurement behavior, or instrumentation; sustained
measurements were not rerun and the tiny runs are not sustained evidence.

## Review and controller handoff

The simplification pass used one combined reviewer because there are no
non-test executable changes. It found no actionable changes; protected proof
tests and their helpers remain intact. Static checks passed afterward.

Local `main` is the older `35814e6` (v0.4.1), an ancestor of the supplied lane.
The item-specific diff is measured from `627fa4c`; the diff against local `main`
also contains the substantive restored source and tests. The controller must
check applicability against its current main before publishing the replacement
PR and retain the campaign's Astra/Fable reviews and hosted CI gate. Local
reproduction verifies the shared Linux matrix command body, not six hosted jobs
or six target architectures.

The chief campaign plan and mandate-common file are not exposed in this clone.
The controller must cross-check their Goal Capsule and cited requirements as
recorded in the implementation plan. This is a controller context dependency.
No owner-only decision or held release/change was introduced. There is no
frontend change, so browser screenshots do not apply. All commits remain local;
the clone has no remote, and none was added or sought.
