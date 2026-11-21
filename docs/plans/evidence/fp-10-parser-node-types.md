# Parser node types: build evidence

## Starting state

The clean `drawdown/fp-10` branch started at `9d2c748`, containing the committed
plan over `3290e08`. All four targeted `parse_node()` TODO branches were present.
No remote exists; delivery is by local commits for the campaign controller.
The chief repository and campaign excerpts remain unavailable in this lane.

## Unchanged parser baseline

Measured on Python 3.14.0 with the frozen dependency lock, before production edits.
Both downloaded OWL inputs match the planning inventory byte for byte.

| Published ref | Bytes | Raw classes | Parsed classes | Raw object properties | Parsed object properties | Triples |
|---|---:|---:|---:|---:|---:|---:|
| `2.0.0` | 18,292,334 | 18,324 | 18,323 | 181 | 175 | 130,148 |
| `main` | 18,335,854 | 18,327 | 18,326 | 181 | 175 | 130,628 |

Each input contains 7 datatype properties, 25 annotation properties, 30 named
individuals, and 11 RDF descriptions. All four types therefore require parsing.

Source SHA-256:

- `2.0.0`: `b6ed82e6d17b7cb1d468453e4111ec08ca091d72a6849be2b58dd37692cb6ef9`
- `main`: `44657b4ed844f5f9c9c48869184606b4fc671471a8263d79d241de87809fa239`

The build retains identical bytes and canonical JSON snapshots outside the
repository for the before/after check. Snapshots include complete class/property
models, all legacy IRI/label indexes, class edges, title/description, ordered
triples and cached triples, prefix ranking bonuses, lowercase bridges, and trie
keys. They exclude the intentionally different source tree and new metadata.

Snapshot SHA-256:

- `2.0.0` (71,859,505 bytes): `4e22afc0741dcdff48731698ec1cd46d2cd6133cf48e5dbf18be16304a83abef`
- `main` (72,043,186 bytes): `0c1a414fd50f51096551fcb6a628ec4f20cf07b23f758134a0e37b8491a88389`

Baseline verification:

- `uv run --frozen pytest tests/`, with an isolated core-only wheel interpreter
  configured through `FOLIO_CORE_PYTHON`: **308 passed**, including benchmarks.
- New local characterization and published-count tests: **2 passed** before
  production edits. The local test asserts exact legacy models, indexes and
  triples, then compares metadata-bearing and metadata-free fresh graphs.
- Required Ruff lint/autofix, formatter, and `ty check folio/`: **passed**.

The characterization preserves the actual legacy triple output; it does not
change existing object-property edge generation or refresh semantics.

## Implemented behavior and compatibility

All four dispatch branches now append detached `OWLNode` records to getter-only
tuple collections. Frozen records retain expanded names, immutable attribute
pairs, literal text/tails, ordered nested elements, and optional `rdf:about`.
Processing instructions are omitted without losing their tail text or changing
the source tree. Successful parsing replaces metadata; XML syntax errors retain
previous snapshots. Existing graph parsing and refresh behavior stay intact.

Before implementation, 19 new behavior cases failed because the four accessors
were absent, while the legacy characterization passed. After implementation,
all 35 parser/model cases passed. Added coverage also executes the README snippet
and probes all four accessors from an isolated core-only installed wheel.

On both saved published inputs, the complete post-change legacy snapshots are
byte-identical to the pre-change JSON snapshots above, including their hashes.
The published integration test separately compares fresh full and metadata-free
graphs, asserting identical counts, models, indexes, edges and triples. The
original production XML is unchanged.

Implementation verification before review on Python 3.14.0:

- Full suite, with `FOLIO_CORE_PYTHON` configured: **332 passed** in 30.39 seconds,
  including benchmarks and all three isolated wheel probes. No skips or network
  failures occurred.
- Ruff lint/autofix and formatting, `ty check folio/`, and `git diff --check`:
  **passed**.

The package remains at version `0.4.2`; publishing configuration is unchanged.
No UI changed, so browser screenshots are not applicable. The controller should
carry the README API description to the separate public documentation repository
and supply the unavailable campaign excerpts before campaign acceptance.

## Review and final verification

The `ce-simplify-code` full team reviewed reuse, quality, efficiency, test value,
and comments. No code changes were needed. Three optional comment-removal
suggestions were declined to retain the module documentation convention and
explanations of XML tail preservation and metadata reset ordering.

The `ce-code-review` full review covered correctness, testing, project standards,
and maintainability at `c291ca1`. Run `20261121-072602-5a220221` retained one
finding: the mixed-content test saved its source bytes after capture, leaving
capture-time mutation insufficiently tested. Both testing and maintainability
identified the gap. Independent validation confirmed that clearing processing
instruction tails after snapshot capture could still pass that test.

The additive `test_direct_capture_preserves_source_xml` now serializes an
independently constructed element before calling `parse_node()` and compares the
same source afterward. It includes repeated definitions and mixed text around
processing instructions. A verification-only in-memory mutant that clears the
source tails fails at the new byte comparison; normal parsing passes. No existing
test was edited to address the finding. No actionable review finding remains.

The review dismissed a suggested tuple-builder/cache redesign: the published
collection sizes copy only 811 prior references across 73 records, and no
observed workload or requirement justified the extra state. Cross-model review
was disabled by the checkout; campaign review remains the controller's gate.

Final checks after the review fix:

| Check | Result |
|---|---|
| Full suite on Python 3.14.0, including benchmarks and isolated core-only wheel | **333 passed**, zero skips, 30.08 seconds |
| Deterministic coverage on Python 3.14.0 | **264 passed**, **80.98%**, above the 58% floor |
| Deterministic coverage on Python 3.10.19 | **254 passed**, **71.55%**, above the 58% floor; 10 existing optional kaos skips because kaos requires Python 3.13+ |
| Ruff lint/autofix and formatting; `ty check folio/` | **Passed** |
| Existing test function ASTs against the starting commit | All **164 unchanged** |
| Parser TODO check | **Zero** TODOs in `parse_node()` |
| Public-safe diff and whitespace | No machine-local paths in changed documentation; `git diff --check` passed |

Coverage used the repository's deterministic selection (`tests/` excluding
`tests/test_folio.py`) with branch coverage and `--cov-fail-under=58`. Each Python
environment had its own installed core-only wheel configured through
`FOLIO_CORE_PYTHON`. The final test addition changes no package source, so the
historical snapshot comparison and installed-wheel build remain applicable.

The regression test already preserves the review lesson; no separate solution
document is needed. Browser verification has no affected route for this library
change. No push, PR, remote CI watch, release, or deployment was attempted.
