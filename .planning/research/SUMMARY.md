# Research Summary: Case-Insensitive Prefix Search

**Synthesized:** 2026-04-07
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md
**Confidence:** HIGH — all claims verified against `graph.py` source with specific line numbers

## Executive Summary

All four research dimensions converge on the same architecture: a parallel lowercase `marisa-trie` alongside the existing case-sensitive trie, bridged back to original-case label dicts via a `Dict[str, List[str]]` reverse mapping. No new dependencies required. The implementation touches exactly four locations in `graph.py`.

## Key Recommendations

### Stack
- **`marisa_trie.Trie`** — second instance adds ~1-2 MB RAM, negligible for ~18K labels
- **`str.casefold()`** — use everywhere instead of `str.lower()`; handles Unicode edge cases (German sharp-s); Python 3 is not locale-dependent
- **`Dict[str, List[str]]` bridge dict** — plain Python `defaultdict(list)`; maps `casefold(label)` back to list of original-case labels

### Architecture — "parallel index with bridge dict"
```
case_sensitive=False
  -> _lowercase_label_trie.keys(prefix.casefold())   # ["securities fraud", ...]
  -> _lowercase_to_original["securities fraud"]       # ["Securities Fraud"]
  -> label_to_index["Securities Fraud"]               # [42]
  -> self.classes[42]                                  # OWLClass
```
One resolution path, two entry points. The existing `label_to_index` / `alt_label_to_index` dicts remain source of truth.

### Table Stakes (all interdependent — ship as one unit)
- `case_sensitive: bool = False` parameter on `search_by_prefix()`
- Parallel lowercase trie (`_lowercase_label_trie`) built in `parse_owl()`
- Reverse mapping dict (`_lowercase_to_original`) built with `defaultdict(list)`
- Separate case-insensitive cache (`_ci_prefix_cache`) keyed by `prefix.casefold()`
- Pure-Python fallback updated with same `casefold()` logic
- IRI-based deduplication using a `seen` set on integer indices

### Defer (out of scope)
- NFKD normalization, locale-aware folding, fuzzy prefix matching

## Critical Pitfalls

1. **Duplicate OWLClass results** — "DUI" and "Dui" both fold to "dui"; bridge dict must be `List[str]`, result assembly must deduplicate by index
2. **Scalar assignment drops labels** — `lower_to_original[key] = label` overwrites; must use `defaultdict(list).append()`
3. **Single cache produces heisenbug** — use two separate caches (case-sensitive and case-insensitive)
4. **`refresh()` leaves structures stale** — pre-existing bug; fix by resetting both caches at top of trie-building block in `parse_owl()`
5. **Pure-Python fallback divergence** — must update both paths simultaneously

## Scoping Decisions Needed

- **`MIN_PREFIX_LENGTH = 3`** (line 125) filters out 2-char queries like "IP". Issue #15 mentions "ip" as expected use case. Lower to 2, or document the limitation?
- **Pre-existing `_prefix_cache` staleness in `refresh()`** — fix in same PR (recommended) or separately?

## Roadmap Implications

4 natural phases: (1) data structure declarations, (2) index building in `parse_owl()`, (3) search logic + fallback, (4) tests. Phases 1-2 are zero-behavioral-change. Phase 3 is the only behavioral change.

---
*Synthesized: 2026-04-07*
