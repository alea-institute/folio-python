# Sustained search-cache pressure

These offline benchmarks exercise the v0.4.1 search-cache limits through public
search methods. Production code, package dependencies, and existing benchmarks
are unchanged. Run from the repository root with the locked development and
search dependencies:

```bash
uv sync --locked
uv run pytest tests/test_cache_pressure.py
```

The short command checks capacity, FIFO versus LRU eviction, hot reuse,
case-folded keys, positive results after eviction, trie/fallback parity, runner
cleanup, deadlines, and the installed pytest plugins. It skips the three sustained
cases. Existing tests and benchmarks retain their normal selection and coverage.

## Run sustained pressure

```bash
uv run pytest tests/test_cache_pressure.py -m cache_pressure --run-cache-pressure --no-cov --benchmark-json=/tmp/fp2-cache-pressure-raw.json
```

For one scenario:

```bash
uv run pytest 'tests/test_cache_pressure.py::test_long_cache_pressure[fuzzy-mixed]' --run-cache-pressure --no-cov
```

The other scenario IDs are `prefix-sensitive` and `prefix-insensitive`. All three
take at least three minutes together, plus preparation. Each scenario must meet
all of these conditions in one continuous invocation:

| Criterion | Required value |
|---|---:|
| Measured duration | At least 60 seconds |
| Observed cache misses after baseline | At least 12,800 |
| Memory checkpoints after baseline | At least 10 |
| Cooperative deadline | Less than 180 seconds |
| Cache capacity | 128 entries |

A late batch cannot turn an expired run into a pass. Failures include elapsed
seconds, actual misses, and completed checkpoints. Skips, deselections, and smoke
tests do not provide sustained-pressure evidence.

Coverage must be inactive; the command deliberately uses `--no-cov`. Disabled
benchmarks, cProfile, disabled GC, external trace/profile hooks, and pre-existing
tracemalloc sessions are rejected. Each target uses one pedantic round, one
iteration, and zero plugin warmup rounds. The fast plugin probe verifies exactly
one call against the installed pytest-benchmark version. The benchmark table
reports the entire harness duration, including graph preparation and cleanup;
it is not per-request latency.

## Workload and measurement boundaries

The generated RDF/XML has 263 classes, 263 nonempty definitions, and 523 alternate
labels. Normal `FOLIO` construction parses this fixed dataset and builds real
indexes and tries. Only the loader and optional LLM initialization are replaced;
these tests need no network data or provider account.

The traffic uses 260 classes: a cold cycle of 256 keys and four hot keys. Each
four-request group contains two cold requests followed by the same hot request
twice. Every request must return its known class; fuzzy requests must also return
the exact score of 100. Prefix queries match both a primary and alternate label
of that class, exercising deduplication. The mixed fuzzy scenario alternates
public alternate-label searches and definition searches through the shared LRU.

Both prefix caches are per-instance FIFO caches; reads do not promote entries.
The insensitive cache uses case-folded keys. Prefix misses are observed by
checking the actual normalized key immediately before each call. Fuzzy misses
come from `_basic_search.cache_info()` deltas; label and definition keys compete
for one shared process-wide cache. Repeating a cold key is counted as a miss only
when it has actually been evicted. Warmup overlap may produce initial hits.

Tracing starts before graph construction. The selected paths are warmed and the
selected cache filled to 128 entries before an explicit GC, baseline sample, and
peak reset. One graph and its caches remain alive for the entire interval.
Normal GC stays enabled. Requests run in batches of 64; checks and GC memory
samples happen between batches. Each result is released before sampling.
Checkpoints occur at least five seconds apart, without sleeping. Baseline,
checkpoint, and final memory samples use the same explicit collection policy.

The harness retains counters, the first eight and last eight batch durations,
and the most recent 16 checkpoints. It retains no per-request keys, results,
timings, or memory snapshots. Reports are formatted after measurement. Cleanup
clears the global fuzzy cache and stops tracing owned by the runner, including
after failures; a tracing session owned by someone else is left running.

## Public evidence

The committed record is
[`fp-2-cache-pressure.json`](../plans/evidence/fp-2-cache-pressure.json). It records
the tested revision, interpreter and tool versions, and all three completed
scenarios. Raw pytest-benchmark JSON includes host metadata and must remain
temporary. Extract only the harness's explicit report fields and public version
identifiers when preparing an evidence record:

```bash
uv run python - <<'PY'
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path

raw = json.loads(Path('/tmp/fp2-cache-pressure-raw.json').read_text())
scenarios = [b['extra_info']['cache_pressure'] for b in raw['benchmarks']]
assert {r['scenario'] for r in scenarios} == {
    'prefix-sensitive', 'prefix-insensitive', 'fuzzy-mixed'
}
assert len(scenarios) == 3 and all(r['outcome'] == 'complete' for r in scenarios)
evidence = {
    'schema_version': 1,
    'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'python': platform.python_version(),
    'tools': {name: importlib.metadata.version(name) for name in (
        'folio-python', 'pytest', 'pytest-benchmark', 'pytest-cov',
        'marisa-trie', 'rapidfuzz',
    )},
    'scenarios': scenarios,
}
print(json.dumps(evidence, indent=2, allow_nan=False))
PY
```

Use a clean, committed implementation revision when measuring and extracting;
otherwise a HEAD identifier alone does not identify the tested code. Inspect the
extracted JSON before committing. The test module fixes the report's top-level
field allowlist and bounds its collection sizes. Do not copy the raw plugin's
machine information, commit metadata object, environment, or output paths.

## What the results establish

Entry-count and correctness assertions are strict. Python-traced memory deltas
and instrumented early/late batch timings are observations, without guessed byte
or latency thresholds. Samples include Python allocations from the harness and
other graph helpers; transient allocation peaks and allocator reuse affect them.
Data created before tracing (including the RDF/XML string), native allocations,
and total process RSS are outside tracemalloc's measurement.

These are finite measurements on a small deterministic dataset. They do not
establish a total process-memory bound, production latency guarantee, or absence
of leaks over unlimited runtime. Larger ontologies, different payload sizes,
native trie allocations, other helper caches, and application state need their
own measurements. Compare runs with matching dataset, criteria, versions, and
instrumentation; the single-round benchmark table is not a statistical latency
distribution.
