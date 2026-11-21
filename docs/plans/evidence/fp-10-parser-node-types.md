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
