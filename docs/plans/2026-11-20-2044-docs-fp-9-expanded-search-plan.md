---
title: Document fp-9 expanded search - Plan
type: docs
date: 2026-11-20
artifact_contract: ce-unified-plan/v1
product_contract_source: ce-plan-bootstrap
execution: code
item: fp-9
kind: expansion
branch: drawdown/fp-9
---

# Document fp-9 expanded search - Plan

## Goal Capsule

- **Objective:** Downstream FOLIO developers can choose query expansion, run an example, and interpret its results and fallback behavior.
- **Means:** Document the existing method and exercise an importable example against a stub LLM (KTD1, KTD2).
- **Authority:** The controller's `fp-9` mandate and standing rules, plus `CLAUDE.md` and `CONTRIBUTING.md`. Campaign authority is the chief repository's `docs/plans/2026-10-26-0705-feat-codex-drawdown-campaign-plan.md`, Goal Capsule and campaign R11, R15, R16, R17, R19, R20.
- **Source limitation:** The chief repository, campaign plan, and `ops/drawdown/mandates/_common.md` are not available in this lane. Their text has not been independently read; campaign citations below derive from the supplied standing rules. The controller must provide those excerpts for campaign acceptance.
- **Delivery:** This stage commits only this plan. The later build stage runs `lfg` on it and delivers one expansion in one PR under R6; the controller publishes and the campaign gate merges.
- **Stop conditions:** Preserve R4–R7. Report unavailable verification separately from passing checks; no user decision is needed for the specified documentation work.

## Product Contract

### Summary

Add a README section explaining `FOLIO.search_expanded()` and a runnable `examples/expanded_search.py` with an importable async core. Add offline tests that execute that core through the real public search method.

### Problem Frame

Query expansion merged in #29, but neither `README.md` nor `examples/` mentions it at the inspected starting commit. Developers cannot discover when to use it or distinguish its result objects from the tuples returned by other search methods.

### Requirements

Local R-IDs belong to this item; references prefixed **campaign** identify the supplied campaign rules.

**Documentation and example**

- R1. The README explains when query expansion helps, its fallback to original-query search, and the arguments exactly as the public method defines them.
- R2. The README explains the returned result and hit fields, including `expansion_source`, and links to `examples/expanded_search.py`.
- R3. The example's core path runs in a test offline against a stub LLM, returns hits and an `expansion_source`, and makes no network request or live LLM call or API-key lookup.

**Compatibility and delivery**

- R4. Preserve `folio/expansion.py` behavior, existing public APIs, every existing test and assertion, package versions, and PyPI publishing configuration.
- R5. Add tests for the example and keep the full repository suite and required lint, format, and type checks passing (campaign R15, R16).
- R6. Work only on `fp-9` in `drawdown/fp-9`, committing locally without adding a remote or seeking credentials; the controller scans, pushes, and opens the PR (campaign R15, R17, R19).
- R7. Exclude migrations, data rewrites, new outside services, spend, credential/security changes, sends in the user's voice, unbacked deletion, and force-push; never read the prohibited secret files (campaign R11). Report genuine missing prerequisites under campaign R20.

### Key Decisions

- **Expansions merge through campaign guardrails.** Governs R5, R6. (session-settled: user-directed — chosen over holding expansions for personal review: the campaign gate owns acceptance.)
- **The mandate bounds this branch.** Governs R6, R7. (session-settled: user-directed — chosen over speculative features after assigned work: remaining campaign work follows the ordered mandate and durable-hygiene policy.)

### Scope Boundaries

The intended implementation changes are `README.md`, `examples/expanded_search.py`, and `tests/test_expanded_search_example.py`, plus this plan. The library implementation, dependency manifests, lockfile, existing examples, and existing tests need no changes.
No front-end page changes are proposed, so the campaign screenshot requirement does not apply.

Provider-selection advice, model prices, new expansion options, cache changes, and ranking changes are outside this item. An offline ontology mode or a general provider adapter in the example is unnecessary: the existing test fixture already supplies a local graph. Reconsider only if that fixture cannot exercise the example's real search path.

## Planning Contract

### Verified Starting State

- The initial worktree was clean on `drawdown/fp-9` at `d79f4a742b54ffe646fc69d8b1df7e031d112cf0`. The local `main` ref is `35814e6e405c3a17d7a2240d8ea0efe7b4179461`, 14 commits behind this branch with no unique commits; preserve the supplied branch base. No remote is configured.
- `folio/graph.py` defines the async public method; `folio/expansion.py` owns expansion, caching, fusion, and result dataclasses. `pyproject.toml` is version `0.4.2`.
- Searching `README.md` and `examples/` found no `search_expanded` or `expanded_search` reference. `tests/test_expansion.py` already covers expansion success, cache reuse, provider failure, timeout, and empty queries.
- `tests/conftest.py::local_graph` replaces ontology loading and disables default LLM initialization. Tests attach their stub to `graph.llm` after construction. `tests/test_structured_query_examples.py` loads example modules by file path because examples are excluded from the distribution.
- No runtime tests were run during planning. Existing receipts do not establish the current suite result; the build stage must establish its own baseline.

### Public Contract to Document

These names and defaults come from `FOLIO.search_expanded` and its imported constants, not the lower-level module function's additional tuning parameters.

| Argument | Default | Meaning |
| --- | --- | --- |
| `query` | Required | Natural-language query to expand and search |
| `limit` | `10` | Maximum returned hits; use positive values |
| `include_definitions` | `True` | Also search definitions, at lower weight |
| `max_expansions` | `8` | Number of expansion terms, bounded to 0–10; `0` disables expansion |
| `timeout` | `10.0` | LLM-call timeout in seconds, not a deadline for the whole search |

The method returns `ExpandedSearchResult` with `query`, `expansions`, `hits`, `expansion_source`, `expansion_error`, `elapsed_ms`, and `usage`.
Each `ExpandedSearchHit` contains `owl_class`, `score`, and `matched_via`; labels and IRIs come from `hit.owl_class`.
The score is a fusion score, not a probability or the underlying search's 0–100 score. Exact original-label anchors can affect result order, so do not promise strict score ordering.
`to_dict()` produces JSON-serializable metadata and a `results` list containing `iri`, `label`, `score`, and `matched_via`; it does not serialize `usage` or use `hits` as the list key.

`expansion_source` is `"llm"` for new terms, `"cache"` for reused/shared terms, or `"none"` when no terms are used.
If expansion is disabled or no usable terms are available after an absent LLM, failure, timeout, invalid response, or open circuit, search still uses the original query.
The implementation searches definitions whenever `include_definitions=True`, including without expansions; `False` gives label-only fallback.
LLM failures are contained, but original-query search failures can propagate. The `[search]` extra remains the documented prerequisite; fallback does not make fuzzy search a core-only feature.

### Key Technical Decisions

- KTD1. **Document the wrapper's actual contract.** Use the table and result descriptions above for R1, R2; do not expose lower-level fusion controls as public-method arguments. Describe query expansion as producing search terms for ordinary ontology search, distinct from asking an LLM to score candidate classes.
- KTD2. **Keep graph construction outside the example's async core.** The core receives an initialized `FOLIO` graph and returns the real `ExpandedSearchResult`. Follow `examples/structured_queries.py` for import safety and `tests/test_expansion.py::FakeLLM` for the async `json_async` response shape (`data`, optional usage metadata). Tests must not mock `search_expanded` or replace its returned hits.
- KTD3. **Use existing offline and import seams.** Follow `local_graph` and the file-path loader in `tests/test_structured_query_examples.py`. Force RapidFuzz through the existing `FOLIO_SEARCH_BACKEND` setting in the new tests only, so fixture expectations do not depend on whether optional kaos is installed.
- KTD4. **Keep the campaign's model and review routing.** (session-settled: user-directed — chosen over the Sol-first ladder: local work uses Astra; cloud builds use the cloud default model and cloud PRs still receive Astra and Fable reviews.) The lane's `cross_model_review_mode: off` is not evidence that the later campaign gate ran.

### Assumptions and Dependencies

- Recommended example presentation: a small deterministic demo LLM supplies fixed terms for a fixed sample query, with an import-safe `asyncio.run` entry point. Pass that stub explicitly during graph construction so the demo does not select the default real provider. Explain how callers use their own configured graph for real expansion. This is an example-design assumption, not a library behavior change.
- The script may load the public ontology through normal `FOLIO` initialization; label that clearly. The required offline guarantee applies to the tested core using `local_graph`, not to a claim that the standalone script downloads nothing.
- The chief-plan excerpts are a controller context dependency, not a personal login or product decision. Available source and the supplied mandate suffice to specify this item; the missing text must be checked before campaign acceptance.
- Full-suite ontology availability and actual baseline results remain execution-time checks. Dependency caches are under `XDG_CACHE_HOME`; do not seek credentials to repair environment failures.

## Implementation Units

### U1. Add an importable expanded-search example with offline proof

**Goal:** Give readers an executable example and prove its real search path without a provider.

**Requirements:** R2–R7; KTD2, KTD3.

**Dependencies:** Existing public method and `local_graph`; no new package or service.

**Files:** Create `examples/expanded_search.py` and `tests/test_expanded_search_example.py`.

**Approach:**

1. Expose a small async example callable taking a graph and query, forwarding the documented options, and returning the result object. Keep construction and output under a main guard; use the demo presentation assumption above.
2. Show the expansion terms, source, and each hit's label, IRI, fusion score, and matching terms. Explain that the fixture/sample terms illustrate ontology lookup rather than guarantee live-ontology results.
3. Load the actual example from its repository path in tests and pass a synthetic graph with labelled and defined concepts such as Landlord, Landlord Negligence, and Warranty of Habitability. Stub only the LLM and external loading boundaries.

**Patterns to follow:** `examples/structured_queries.py`; `tests/test_structured_query_examples.py::load_recipes`; `tests/conftest.py::local_graph`; `tests/test_expansion.py::FakeLLM`.

**Test scenarios:**

- Import the module with graph construction guarded to fail; importing must neither construct a graph nor invoke a model.
- Call the core with the sample natural-language query and a stub returning fixture-matching expansion terms. Assert nonempty hits, a known fixture IRI, `expansion_source == "llm"`, the returned terms, and matching-term metadata; confirm the stub was called.
- With `include_definitions=False`, a fresh graph, a label-matching query, and an absent or raising stub, assert nonempty original-query hits, empty expansions, and `expansion_source == "none"`. Compare hit IRIs with the corresponding plain label search, not raw scores.
- With `max_expansions=0`, assert original-query hits, source `"none"`, and zero stub calls. This covers the documented opt-out through the example itself.
- Serialize a successful example result and assert the outer dictionary's `expansion_source` is `"llm"`; each `results` entry contains `iri`, `label`, `score`, and `matched_via`. Avoid assertions on timing, exact fusion scores, or live labels.

**Verification:** The new test module executes the real example core with network entry points guarded to fail and default provider initialization disabled. It proves example/API integration; it does not measure a live provider's quality or availability. Existing expansion regression tests remain unchanged.

### U2. Explain discovery, arguments, fallback, and results in the README

**Goal:** Let a reader choose and run expanded search without inspecting implementation source.

**Requirements:** R1, R2, R4–R7; KTD1.

**Dependencies:** U1 supplies the runnable example and its tested names.

**Files:** Modify `README.md`; extend `tests/test_expanded_search_example.py` only as needed to exercise the documented call.

**Approach:** Add a section near the existing search/LLM sections with a natural-language use case, `[search]` installation prerequisite, async usage, the five public arguments, result fields, and fallback semantics from the contract above. Link the example and its offline test. Keep unrelated provider recommendations and historical benchmarks unchanged.

**Test scenarios:**

- Exercise the documented invocation through U1's actual example helper on the local graph. Every keyword in the snippet must be accepted by the real method, with no provider/key setup in the test.
- Check the README argument names and defaults against the public wrapper and its constants; verify object fields and the `hits` versus serialized `results` distinction against the dataclasses. Use focused review rather than a brittle full-text snapshot test.

**Verification:** The README snippet agrees with the executable example and documented contract; the linked files exist. U1's offline tests back the usage claims, while source review catches prose and default-value drift.

## Verification Contract

The build first records a fresh baseline, then verifies the completed change using `CLAUDE.md` and `CONTRIBUTING.md` as the command authorities.

| Check | Scope | Required evidence |
| --- | --- | --- |
| Focused tests | `tests/test_expanded_search_example.py` and `tests/test_expansion.py` | Offline example success, fallback, opt-out, serialization, and unchanged expansion regressions pass |
| Full suite | `uv run --frozen pytest tests/` | All existing tests, integration coverage, and benchmarks pass; report network failures separately |
| Core-only installation | `CONTRIBUTING.md` isolated installation with `FOLIO_CORE_PYTHON` supplied | Existing core-only check executes rather than relying on its environment-dependent skip |
| Lint and format | Existing required checks over `folio/` and `tests/`, plus the new example file | No new findings or formatting differences |
| Types | `uv run --frozen ty check folio/` | Zero diagnostics |
| Documentation and scope | Public wrapper, dataclasses, README call, and branch diff against the recorded starting commit | Exact documented names; only this item's intended changes; R4, R6, R7 preserved |

Use existing locked dependencies. Do not satisfy a failed check by changing expansion behavior or deleting, skipping, or weakening a test. No browser launch or screenshot is needed for this documentation/example-only change.

## Definition of Done

- U1 and U2 meet their verification outcomes, including an offline test that runs the example's real core and asserts hits plus `expansion_source`.
- The README accurately describes the public arguments, fallback behavior, and result fields; existing expansion behavior and tests are preserved.
- Required checks pass, with any unavailable environment evidence reported explicitly; remove abandoned code introduced during implementation without disturbing pre-existing work.
- Local commits on `drawdown/fp-9` contain the implementation and evidence needed for controller publication under R6. This plan-stage commit alone is not implementation acceptance.
