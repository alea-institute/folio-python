# Technology Stack

**Project:** folio-python — case-insensitive prefix search
**Researched:** 2026-04-07
**Confidence:** HIGH (all claims verified from source code)

## Current Stack

### Core Dependencies (required)

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | >=3.10, <4 | Runtime; `str.casefold()` available since 3.0 |
| pydantic | >=2.8.2 | OWLClass model validation |
| lxml | >=5.2.2 | OWL/XML parsing |

### Search Dependencies (optional extras: `folio-python[search]`)

| Technology | Version | Purpose |
|------------|---------|---------|
| marisa-trie | >=1.2.0, <2 | Compressed prefix trie for `search_by_prefix()` |
| rapidfuzz | >=3.10.0, <4 | Fuzzy label matching for `search_by_label()` |
| alea-llm-client | >=0.1.1 | LLM-assisted search |

## marisa-trie API for This Feature

The feature uses exactly two marisa-trie operations — both already in use in the codebase.

### Construction (`graph.py:1005-1012`)

```python
self._label_trie = marisa_trie.Trie(all_labels)
```

`marisa_trie.Trie(iterable)` accepts any iterable of `str`. To build the parallel lowercase trie, pass the same label list with `casefold()` applied:

```python
self._lowercase_label_trie = marisa_trie.Trie(
    label.casefold() for label in all_labels
)
```

### Prefix lookup (`graph.py:1306-1309`)

```python
keys = sorted(self._label_trie.keys(prefix), key=len)
```

`trie.keys(prefix: str) -> List[str]` returns all stored strings that start with `prefix`. For the lowercase trie, pass `prefix.casefold()` as the query:

```python
keys = sorted(self._lowercase_label_trie.keys(prefix.casefold()), key=len)
```

No other marisa-trie API surface is needed.

## No New Dependencies Required

The parallel trie approach uses only constructs already present in the codebase:

- `marisa_trie.Trie` — already imported and guarded at `graph.py:138-142`
- `str.casefold()` — Python stdlib, no import
- `dict` bridge (`_lowercase_to_original: Dict[str, List[str]]`) — plain Python

The pure-Python fallback path (`graph.py:1312-1320`) requires only `str.casefold()` and `str.startswith()` — also no new imports.

## Memory and Performance

| Concern | Assessment |
|---------|------------|
| Second trie size | MARISA compression on ~18K short label strings produces a trie of roughly 1-2 MB. A second trie over the same labels (casefolded) is the same order of magnitude — negligible. |
| Build time | Trie construction runs once during `_load_folio()`. Adding a second `marisa_trie.Trie(...)` call adds milliseconds. |
| Lookup performance | `trie.keys(prefix)` is O(|prefix| + |results|) — identical for both tries. |
| Cache overhead | Two separate `_prefix_cache` dicts (one per `case_sensitive` flag value). At ~18K concepts, worst-case cache size is still small. Alternatively, normalize cache key to `(prefix.casefold(), case_sensitive)` tuple to share entries across case variants when `case_sensitive=False`. |
| Bridge dict | `_lowercase_to_original: Dict[str, List[str]]` maps each casefolded label back to its original-case form(s). Required because `trie.keys()` on the lowercase trie returns casefolded keys; those must resolve to the original `label_to_index` / `alt_label_to_index` lookups. At 18K entries this dict is trivially small. |

## `casefold()` vs `lower()`

Use `str.casefold()` throughout — not `str.lower()`.

- `casefold()` is the Python-idiomatic choice for case-insensitive comparison (PEP 3131, Python docs).
- It handles Unicode edge cases `lower()` misses (e.g., German `"ß".casefold() == "ss"`, not `"ß"`).
- FOLIO labels are currently ASCII/Latin-1, so the difference is moot today — but `casefold()` is correct-by-default for future robustness.
- Consistent use of the same normalization function at build time and query time is what matters most; `casefold()` satisfies this.

## Implementation Touchpoints

| Location | Change |
|----------|--------|
| `graph.py:1004-1012` | Add `self._lowercase_label_trie` and `self._lowercase_to_original` dict alongside existing trie build |
| `graph.py:1289` | Add `case_sensitive: bool = False` parameter to `search_by_prefix()` |
| `graph.py:1300-1330` | Branch on `case_sensitive`; use lowercase trie + bridge dict when `False`; normalize cache key |
| Pure-Python fallback (`graph.py:1312-1320`) | Add `label.casefold().startswith(prefix.casefold())` branch |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Case normalization | `casefold()` | `lower()` | `lower()` misses Unicode edge cases; `casefold()` is the stdlib-blessed choice |
| Architecture | Parallel trie + bridge dict | Single trie with post-filter | Post-filter forfeits O(prefix) trie advantage; scans all keys |
| Architecture | Parallel trie + bridge dict | Case-normalize labels in-place | Destroys original-case labels needed for display and downstream lookups |
| Cache design | Per-flag cache or tuple key | Single shared cache | Without normalization, `"securit"` and `"Securit"` would produce duplicate entries |
