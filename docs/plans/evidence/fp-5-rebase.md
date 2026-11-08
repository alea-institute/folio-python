# fp-5 build preflight: blocked before rebase

Date: 2026-11-08. Item: `fp-5` (expansion). Branch: `drawdown/fp-5`.
Plan: `docs/plans/2026-11-08-0825-fix-fp-5-benchmark-rebase-plan.md`.

**Status:** The supplied branch's baseline passes. The benchmark series has not
been integrated, no sustained fp-5 measurements exist, and this receipt does not
establish acceptance or supersede PR #24. Execution stopped at U1's source and
target provenance prerequisites. U2 and U3 depend on U1 and remain unexecuted.

## Reverified identities

| Role | Commit | Observed status |
| --- | --- | --- |
| Original fp-5 tip and committed plan | `056787ef4fab072823ad500f98be0bfd5385126e` | Clean starting checkout; all baseline checks below tested this revision. |
| Supplied branch parent | `1a59da2be0dd87da02a815a9e2ee44431c6bc696` | Contains fp-1, fp-3, and fp-4; not independently confirmed as current upstream main. |
| Local main | `35814e6e405c3a17d7a2240d8ea0efe7b4179461` | Tagged v0.4.1; older than the supplied branch parent. |
| Retained fp-2 candidate | `4ce874c9fdfe5e59a997a43f096f5ff23461b7b1` | Commit exists, but neither `drawdown/fp-2` nor `origin/drawdown/fp-2` exists. Correspondence to PR #24's complete head remains unconfirmed. |
| Candidate/supplied-tip common ancestor | `06557c913164c5a15ca4075d0fc274c09768f64a` | Recomputed with `git merge-base`. |

The candidate contains the four commits identified by the plan, oldest first:
`59ffcb4` (plan), `fc55e13` (cache characterization), `58c5369` (sustained
measurement), and `4ce874c9` (documentation and results). Relative to the common
ancestor it changes six files with 1,475 insertions. It does not change production
code or the lockfile.

The following local recovery refs were created and read back, without moving any
existing branch or rewriting history:

- `refs/drawdown-recovery/fp-5/original-tip` points to `056787ef4fab072823ad500f98be0bfd5385126e`.
- `refs/drawdown-recovery/fp-5/source-candidate` points to `4ce874c9fdfe5e59a997a43f096f5ff23461b7b1`.
- `refs/drawdown-recovery/fp-5/target-candidate` points to `1a59da2be0dd87da02a815a9e2ee44431c6bc696`.

These refs preserve available recovery material; they do not authenticate source
or target provenance. They are local refs, not additional item branches, and are
not included by an ordinary push of `drawdown/fp-5`.

## Integration findings

Read-only `git merge-tree 06557c9 1a59da2 4ce874c9` confirms a content conflict in
`pyproject.toml` and an add/add conflict in `tests/conftest.py`.

The required resolution remains the plan's KTD2: retain the supplied parent's
branch-coverage options, typing configuration, and `local_graph` fixture, while
adding the candidate's pressure marker, opt-in option, collection hook, and
`pytester` plugin. Neither file can be resolved by selecting one side wholesale.

Static inspection also reconfirms KTD3: the candidate's backend parity test
disables the module-level MARISA dependency after graph construction, leaving
existing trie instance fields populated. The resumed implementation must build
and assert a separate fallback graph and add the combined-conftest subprocess
regression. No backend repair or new regression test is claimed here.

## Baseline verification

Environment: Linux, Python 3.13.11 in both project and isolated core environments,
uv 0.9.22, pytest 9.1.1, pytest-benchmark 5.2.3, pytest-cov 7.1.0, Ruff 0.15.6,
ty 0.0.92, marisa-trie 1.4.0, and rapidfuzz 3.14.3.

| Check at original tip `056787e` | Result |
| --- | --- |
| `uv sync --frozen --no-default-groups --group dev --extra search` | Passed; frozen dependency inputs unchanged. |
| Isolated core wheel install with `uv sync --frozen --no-default-groups --no-editable` and a separate `UV_PROJECT_ENVIRONMENT` | Passed. |
| `uv run --frozen ruff check folio/ tests/` | Passed. |
| `uv run --frozen ruff format --check folio/ tests/` | Passed; all 16 files already formatted. |
| `uv run --frozen ty check folio/` | Passed; zero diagnostics. |
| `uv run --frozen pytest tests/` with `FOLIO_CORE_PYTHON` set to the isolated interpreter | **149 passed in 32.21 seconds; zero skips**, including 10 existing benchmarks, live ontology tests, and the core-only installation test. Reported combined coverage: 91% (rounded). |

Raw logs and generated coverage outputs remain uncommitted. These checks cover
the unintegrated supplied branch only. The three sustained cache-pressure cases,
merged-conftest regression, rebased full suite, deterministic coverage gate, and
hosted Python 3.10/3.14 checks have not run for an integrated fp-5 revision.
There is no frontend change, so no browser screenshot applies.

## Controller inputs required to resume

1. Supply the verified complete fp-2 source ref, or explicitly confirm that
   `4ce874c9fdfe5e59a997a43f096f5ff23461b7b1` is PR #24's complete source tip.
2. Supply verified current-main identity, confirming or replacing candidate
   `1a59da2be0dd87da02a815a9e2ee44431c6bc696` and retaining the already integrated
   fp-1, fp-3, and fp-4 work.
3. Confirm fp-5 publication status and supply any published tip. KTD1 requires
   preserving that tip's ancestry rather than silently rewriting published work.
4. Supply the chief campaign plan's Goal Capsule and R11, R15, R16, R17, R19,
   and R20 excerpts. The chief repository is unavailable in this sandbox; the
   supplied standing rules are the only campaign text available here.

These are controller context dependencies, not a request for a login, credential,
or product decision. No remote was configured, credentials sought, push made,
or PR opened. No source, test, dependency, version, or publishing file changed.

Resume U1 after those inputs are supplied, preserve this receipt and all recovery
tips, and execute U2/U3 plus the remaining LFG gates. Add fresh sustained evidence
only after testing a clean committed integrated revision. The controller still
owns opening the replacement PR that explicitly supersedes #24 and recording the
campaign's required reviews and merge checks.
