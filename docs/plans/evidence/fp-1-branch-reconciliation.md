# fp-1 branch reconciliation evidence

Verified locally on 2026-10-26 for
`docs/plans/2026-10-26-0929-fix-fp-1-branch-reconciliation-plan.md`.

## Outcome and limits

The available search changes are already integrated. This change adds ten
deterministic regression cases in `tests/test_search_reconciliation.py` and
preserves the useful U12 preparation history below. Production source, existing
tests, dependencies, versions, and publishing configuration are unchanged.

**The named-branch reconciliation remains provisional.** This clone has no
remote and none of the three named source refs. The controller must confirm the
current source tips and target main before closing R1. Local history proves the
disposition of the observed commits, not the absence of unseen branch changes.

The chief campaign plan and common mandate file are not mounted. Their Goal
Capsule and campaign R11, R15, R16, R17, R19, R20 were not read. The controller's
build-stage instruction authorizes the independent work reported here, including
tests and local commits; it does not supply the missing campaign text. This
records the authority limitation rather than reconstructing those excerpts.

## Starting identities

| Ref or role | Full commit |
| --- | --- |
| Build-stage starting HEAD, `drawdown/fp-1` | `e464cee208f3accec6aeee6123a6e67e09f5b5bd` |
| Plan-stage code baseline | `06557c913164c5a15ca4075d0fc274c09768f64a` |
| Local `main` and `v0.4.1` | `35814e6e405c3a17d7a2240d8ea0efe7b4179461` |

The starting tree was clean. HEAD adds only the committed plan to the plan-stage
code baseline. That code baseline is two commits ahead of local main, changing
one formatting blank line in `folio/graph.py` and adding the October 20 handoff.
No reset, branch merge, cherry-pick, remote setup, or credential lookup was used.

## Observed source dispositions

| Named branch | Observed source evidence | Changed-file inventory and disposition |
| --- | --- | --- |
| `fix/altlabel-lang-search` | Historical tip identified in `docs/handoffs/2026-10-20-sweep-cloud-folio-python.md`: `303eb54063148dcb1ad282d640694a21aedad829` | The aggregate `32f9666^..303eb54` changes only `folio/graph.py`. Its stable patch ID, `6bf1d28e36e0a6f153bd985b6236c37feb1e07dc`, equals main's `b9a1a70caa789e8b16ce38261b9b2bf93a6c3214` (#13). Observed fix integrated; today's branch tip still unconfirmed. |
| `feature/case-insensitive-prefix` | Early implementation `caa7c8531af69e27ac0537a8f4fab8dc4065b9b5`; related candidate histories `7e8b4a4a40446a974398fcc06cac5dfb573750be` and `50f3e315d2ce0abf1b6cd5a1764c00510a9513e4` | The early change touches `folio/graph.py` and `tests/test_folio.py`. Main includes `fe05fd4` (#16); those two files are byte-identical between `50f3e31` and `fe05fd4`. Parsing, refresh, and the public dispatcher also match current HEAD. The prefix helpers have only the later bounded-cache storage change relative to #16. Observed behavior integrated; candidate-to-named-branch mapping remains unconfirmed. |
| `chore/u12-exec-20260930` | Candidate tip `8bd27dfc6ca2ef380950530671eb08087304da20`, preceded by `e96de9ac288fc65a8565c4fbb2fa986aa2f15b6b` | Relative to common ancestor `1b4fb3493815ca7aeb0ce7f454399c19723f9820`, adds only `docs/plans/2026-09-30-release-delivery-reconciliation.md` and `agents/run-notes/u12-exec-folio-python-20260930.md`. Useful facts are retained below; historical publishing instructions and machine-local paths are excluded. Candidate identity remains unconfirmed. |

The related prefix histories are not safe whole-branch substitutes. From their
common ancestors, `50f3e31` includes 24 `.planning/` documents plus graph/tests;
`7e8b4a4` additionally includes `CHANGES.md`, `CLAUDE.md`, `THIRD-PARTY.md`,
`folio/__init__.py`, `pyproject.toml`, and `uv.lock`. The latter carries old
release metadata and lacks newer structured-query code and tests. Main already
removed the historical planning scaffolding in `93d1df8` and carries newer
release and dependency state. None of that superseded material was restored.

Local tags place #13 in `v0.3.4` and later, #16 in `v0.3.5` and later, and the
cache-bound fix `1b4fb34` in `v0.4.1`. These are source-inclusion facts, not proof
of successful package publication. No current PyPI delivery assertion is made.

## U12 preparation facts retained

The September 30 artifacts at `e96de9a` and `8bd27df` tested source `1b4fb34`,
which then declared version 0.4.0. The old task's requested 0.3.7 upload was
already stale; registry delivery remained unknown. That session recorded:

- 15 unchanged IRI tests passing in an offline harness, with optional LLM
  loading and pytest plugin autoload disabled and socket access blocked.
- Ruff passing; wheel and sdist built using cached build tools after an isolated
  build could not find Hatchling.
- Both artifacts declaring 0.4.0 and the runtime floor `lxml>=6.1.0`, alongside
  `httpx>=0.27.2` and `pydantic>=2.8.2`.
- An installed-wheel import/version/IRI smoke passing in an isolated target.

Those checks did not prove clean dependency resolution, full graph/search/LLM
integration, sdist installation, or published artifact delivery. The artifacts
were temporary local candidates, not durable release storage. They were not
rebuilt or published in this lane. Version selection, package publication, and
trusted-publisher setup remain outside fp-1 under the current mandate.

## Current verification

Dependencies were installed from the unchanged lockfile using `uv sync --frozen`.
The runner used Python 3.13.11, pytest 9.1.1, Ruff 0.15.6, MARISA 1.4.0, and
ty 0.0.92. Baseline and final checks used the same project environment. Existing
integration tests used their normal public FOLIO ontology loaders and cache;
their upstream data is live, not a pinned test fixture. The new regressions
supply small in-memory RDF/XML documents through the real parser.

| Check | Actual result |
| --- | --- |
| Baseline `uv run pytest tests/ -k "not benchmark"` | 70 passed, 10 deselected. |
| `uv run pytest tests/test_search_reconciliation.py -v` | 10 passed: five real-MARISA cases and five forced-fallback cases. |
| Focused offline harness | 10 passed with an audit hook rejecting `socket.connect` and `socket.getaddrinfo`; no ontology network needed. |
| Final `uv run pytest tests/` | 90 passed, including all 10 existing benchmarks. |
| Final fast suite | First attempt: 79 passed and one `httpx.ConnectTimeout` in the existing public GitHub branch-list test. Unchanged retry: 80 passed, 10 deselected. |
| Ruff baseline | Check and format check passed. |
| Ruff final | `uv run ruff check --fix folio/ tests/` passed; `uv run ruff format folio/ tests/` formatted only the new test file. |
| Baseline and final types | Both report the same 47 diagnostics; diagnostic text matches exactly after removing tool-install preamble. No new diagnostics. |

`uvx ty` initially could not create its tool directory in the read-only home.
Selecting a writable temporary `UV_TOOL_DIR` allowed the unchanged type-check
command to run. The inherited categories are invalid argument, assignment,
return, and annotation types, plus unresolved imports and attributes. This is
baseline-relative acceptance, not a clean type-check claim.

The added cases cover tagged and untagged duplicate aliases in both XML orders,
preserved translations, Unicode `Straße`/`STRASS` matching, explicit sensitive
mode, primary-label precedence over a shorter alternative, deduplication, cached
repeat calls, and successful refresh of cached primary/alternative hits and
misses. Each backend constructs fresh graphs; MARISA cases require actual tries.
No production change was needed for characterization, and no existing test or
assertion was changed. Cache bounds remain covered by the existing suite.

## Review and delivery

The local code review covered both added files against `e464cee`, the explicit
fp-1 plan, and `CLAUDE.md`. No implementation defect was found. The plan
completeness check retains one P1 acceptance gap: R1 and U1/U3 cannot close
without the controller evidence below. U2 is verified. This is a locally tested
change ready for controller intake, not a claim that the complete mandate item
is reconciled. The review finding cannot be repaired by guessing source tips.

Browser verification is not applicable: these changes add no frontend page or
route. No screenshot is required. No additional learning document is needed;
the plan, tests, and this receipt carry the reconciliation reasoning. Only local
commits are authorized in this clone; push, PR creation, and CI watching are
left to the controller. No held release or migration was introduced.

## Controller acceptance inputs

1. Supply the chief campaign Goal Capsule and cited R-ID excerpts, confirming
   consistency with the supplied standing rules.
2. Supply a dated mapping of the three exact named branches to full tip SHAs and
   the current target-main SHA; make any missing objects available to the lane.
3. Recompare any additional source commits before closing R1 or the whole item.
   The current tests and candidate comparisons cannot prove unseen deltas absent.

These are controller repository-evidence dependencies, not a request for a
personal login, credential, service, or decision. This lane requires no new
Damien decision and does not wait for one. Publication belongs to the controller.
