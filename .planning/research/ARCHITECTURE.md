# Architecture: Parallel Lowercase Trie for Case-Insensitive Prefix Search

**Domain:** FOLIO ontology graph — prefix search subsystem
**Researched:** 2026-04-07
**Confidence:** HIGH (all integration points verified against existing source)

## Current Architecture (Baseline)

### Data Flow: Label Ingestion to Search Result

```
parse_owl_class() [line 740-773]
  |
  +--> label_to_index: Dict[str, List[int]]        # "Securities Fraud" -> [42]
  +--> alt_label_to_index: Dict[str, List[int]]     # "DUI" -> [17]
  |
  v
parse_owl() [line 1004-1012]  (end of method, after all nodes parsed)
  |
  +--> _label_trie: marisa_trie.Trie(all_labels)    # built from both dicts' keys
  |
  v
search_by_prefix("Securit") [line 1289-1333]
  |
  +--> _prefix_cache check (exact prefix string)
  +--> _label_trie.keys("Securit")                  # returns ["Securities Fraud", ...]
  +--> label_to_index / alt_label_to_index lookup    # label -> List[int] indices
  +--> self[index] for each                          # int -> OWLClass via self.classes[index]
  +--> cache result in _prefix_cache[prefix]
```

### Key Data Structures

| Attribute | Type | Purpose |
|-----------|------|---------|
| `label_to_index` | `Dict[str, List[int]]` | Original-case label -> class indices |
| `alt_label_to_index` | `Dict[str, List[int]]` | Original-case alt/preferred label -> class indices |
| `_label_trie` | `marisa_trie.Trie` or `None` | Case-sensitive prefix lookup (keys from both dicts) |
| `_prefix_cache` | `Dict[str, List[OWLClass]]` | Memoized results keyed by exact prefix string |
| `classes` | `List[OWLClass]` | Master list; integer indices resolve to objects |

### Critical Observations

1. **Index-based resolution.** Both `label_to_index` and `alt_label_to_index` map strings to `List[int]` (indices into `self.classes`). The trie only stores keys; it does not store values. The trie's job is prefix-matching; the dicts handle key-to-index resolution.

2. **Pure-Python fallback.** When `marisa_trie` is `None`, `search_by_prefix` falls back to a linear scan of both dicts' keys with `str.startswith()`. The fallback must also gain case-insensitive support.

3. **Cache is prefix-exact.** `_prefix_cache["Securit"]` and `_prefix_cache["securit"]` are separate entries today. No normalization.

4. **Trie is built once** at the end of `parse_owl()`, after all classes have been parsed and indexed. The `refresh()` method calls `parse_owl()` again (after clearing all data structures), so the trie is rebuilt.

5. **`refresh()` clears dicts but not the trie or cache explicitly.** It clears `label_to_index` and `alt_label_to_index` (line 1262-1263) but relies on `parse_owl()` reassigning `_label_trie`. The `_prefix_cache` is not cleared in `refresh()` -- this is a pre-existing issue, but any new attributes should follow the same pattern (or fix it).

---

## Recommended Architecture

### New Data Structures

Add three new attributes to `__init__`:

```python
# Case-insensitive search structures
self._lowercase_label_trie: Optional[marisa_trie.Trie] = None
self._lowercase_to_original: Dict[str, List[str]] = {}
self._ci_prefix_cache: Dict[str, List[OWLClass]] = {}
```

| Attribute | Type | Purpose |
|-----------|------|---------|
| `_lowercase_label_trie` | `marisa_trie.Trie` or `None` | Lowercase prefix lookup |
| `_lowercase_to_original` | `Dict[str, List[str]]` | Maps lowercase key -> list of original-case keys |
| `_ci_prefix_cache` | `Dict[str, List[OWLClass]]` | Cache for case-insensitive results, keyed by lowercased prefix |

### Why a Separate Mapping Dict (Not Embedded in Trie Values)

`marisa_trie.Trie` is a pure key set -- it stores strings, not key-value pairs. (`BytesTrie` and `RecordTrie` can store values, but they add complexity and aren't needed here.) The cleanest approach: use the plain `Trie` for prefix matching, then resolve lowercase keys back to originals via `_lowercase_to_original`, which then feeds into the existing `label_to_index` / `alt_label_to_index` dicts.

An alternative would be `marisa_trie.RecordTrie` mapping lowercase keys to integer indices directly, but this would bypass the existing resolution path and create a parallel index system -- more surface area for bugs, no real performance gain at ~18K entries.

### Data Flow: Lowercase Trie Key to OWLClass

```
search_by_prefix("securit", case_sensitive=False)     # caller input
  |
  +--> normalize: prefix_lower = "securit"
  +--> _ci_prefix_cache check (prefix_lower)
  |
  +--> _lowercase_label_trie.keys("securit")           # ["securities fraud", "security", ...]
  |
  +--> For each lowercase_key:
  |      _lowercase_to_original["securities fraud"]    # ["Securities Fraud"]
  |      _lowercase_to_original["security"]            # ["Security"]
  |
  +--> For each original_key:
  |      label_to_index.get("Securities Fraud", [])    # [42]
  |      alt_label_to_index.get("Securities Fraud", [])# []
  |
  +--> self[index] for each index                      # OWLClass objects
  +--> deduplicate (same OWLClass reachable via label + alt_label)
  +--> cache in _ci_prefix_cache[prefix_lower]
```

### Why `_lowercase_to_original` Maps to `List[str]`, Not `str`

Multiple original labels can collide when lowercased. For example, if FOLIO contained both "DUI" and "Dui" (hypothetical), both lowercase to "dui". The mapping must be `str -> List[str]` to handle this without data loss. In practice, collisions are rare in FOLIO (~18K concepts), but correctness requires the list.

---

## Integration Points

### 1. Build Site: `parse_owl()` (line 1004-1012)

The lowercase trie and mapping dict should be built immediately after the existing trie, in the same method, using the same label pool. This keeps the two tries synchronized and avoids a separate build pass.

```python
# EXISTING (unchanged):
if marisa_trie is not None:
    all_labels = [
        label
        for label in list(self.label_to_index.keys())
        + list(self.alt_label_to_index.keys())
        if len(label) >= MIN_PREFIX_LENGTH
    ]
    self._label_trie = marisa_trie.Trie(all_labels)

    # NEW: build lowercase trie and reverse mapping
    self._lowercase_to_original = {}
    for label in all_labels:
        lower = label.lower()
        if lower not in self._lowercase_to_original:
            self._lowercase_to_original[lower] = [label]
        else:
            if label not in self._lowercase_to_original[lower]:
                self._lowercase_to_original[lower].append(label)
    self._lowercase_label_trie = marisa_trie.Trie(
        list(self._lowercase_to_original.keys())
    )
```

**Build order:** The mapping dict MUST be built before the lowercase trie, because `_lowercase_to_original.keys()` provides the deduplicated lowercase key set for the trie. Building the trie from `[l.lower() for l in all_labels]` directly would include duplicates, which `marisa_trie.Trie` silently deduplicates -- but it is cleaner to build the dict first and derive trie keys from it.

### 2. Search Site: `search_by_prefix()` (line 1289-1333)

Add `case_sensitive: bool = False` parameter. Branch on it.

```python
def search_by_prefix(
    self, prefix: str, case_sensitive: bool = False
) -> List[OWLClass]:
    # Determine cache and effective prefix
    if case_sensitive:
        cache = self._prefix_cache
        effective_prefix = prefix
    else:
        cache = self._ci_prefix_cache
        effective_prefix = prefix.lower()

    # Check cache
    if effective_prefix in cache:
        return cache[effective_prefix]

    # Trie path
    if marisa_trie is not None:
        if case_sensitive:
            keys = sorted(self._label_trie.keys(effective_prefix), key=len)
        else:
            lowercase_keys = sorted(
                self._lowercase_label_trie.keys(effective_prefix), key=len
            )
            # Expand lowercase keys to original keys
            keys = []
            for lk in lowercase_keys:
                keys.extend(self._lowercase_to_original.get(lk, []))
    else:
        # Pure-Python fallback
        all_labels = (
            list(self.label_to_index.keys())
            + list(self.alt_label_to_index.keys())
        )
        if case_sensitive:
            keys = sorted(
                [l for l in all_labels if l.startswith(effective_prefix)],
                key=len,
            )
        else:
            keys = sorted(
                [l for l in all_labels if l.lower().startswith(effective_prefix)],
                key=len,
            )

    # Resolve keys to OWLClass (same as existing)
    iri_list = []
    for key in keys:
        iri_list.extend(self.label_to_index.get(key, []))
        iri_list.extend(self.alt_label_to_index.get(key, []))

    # Deduplicate while preserving order
    seen = set()
    unique_indices = []
    for idx in iri_list:
        if idx not in seen:
            seen.add(idx)
            unique_indices.append(idx)

    classes = [self[index] for index in unique_indices]
    cache[effective_prefix] = classes
    return classes
```

### 3. Cache Strategy

**Two separate caches, not one.** The case-sensitive cache (`_prefix_cache`) is keyed by original-case prefix; the case-insensitive cache (`_ci_prefix_cache`) is keyed by lowercased prefix. This prevents cross-contamination: `_prefix_cache["Securit"]` returns only exact-case matches; `_ci_prefix_cache["securit"]` returns all case variants.

**Normalization on the case-insensitive side:** All lookups into `_ci_prefix_cache` use `prefix.lower()` as the key. This means `search_by_prefix("Securit", case_sensitive=False)` and `search_by_prefix("securit", case_sensitive=False)` share the same cache entry. This is the "shared cache for case variants" behavior the PROJECT.md calls for.

**Alternative considered and rejected:** A single unified cache with a `(prefix, case_sensitive)` tuple key. This works but mixes concerns -- the case-insensitive cache should normalize keys to lowercase, which a tuple key does not enforce. Two caches are simpler and less error-prone.

### 4. `__init__` Initialization (line 217-218)

Add new attributes alongside existing ones:

```python
self._label_trie: Optional[marisa_trie.Trie] = None
self._lowercase_label_trie: Optional[marisa_trie.Trie] = None
self._lowercase_to_original: Dict[str, List[str]] = {}
self._prefix_cache: Dict[str, List[OWLClass]] = {}
self._ci_prefix_cache: Dict[str, List[OWLClass]] = {}
```

### 5. `refresh()` Method (line 1250-1287)

`refresh()` calls `parse_owl()` which rebuilds both tries and the mapping dict. The new `_ci_prefix_cache` should be cleared in `refresh()` -- or, since the existing `_prefix_cache` is not explicitly cleared in `refresh()` either (a pre-existing oversight; `parse_owl` reassigns `_label_trie` but the old cache entries become stale), the safest approach is to reset both caches in `parse_owl()` at the top of the trie-building block:

```python
# At the start of the trie-building section in parse_owl():
self._prefix_cache = {}
self._ci_prefix_cache = {}
```

This fixes the pre-existing staleness issue for the original cache and prevents it for the new one.

---

## Component Boundaries

| Component | Responsibility | Touches |
|-----------|---------------|---------|
| `parse_owl_class()` | Populate `label_to_index`, `alt_label_to_index` | No change needed |
| `parse_owl()` (trie section) | Build both tries + mapping dict | Add lowercase trie + mapping build |
| `search_by_prefix()` | Route to correct trie + cache based on `case_sensitive` | Add branching logic |
| `__init__` | Initialize all data structures | Add 3 new attributes |
| `refresh()` / `parse_owl()` | Reset stale state | Clear both caches |

**Boundary principle:** The `_lowercase_to_original` dict is an internal bridge between the lowercase trie and the existing label dicts. It should never be exposed in the public API. Callers interact only with `search_by_prefix(prefix, case_sensitive=...)`.

---

## Patterns to Follow

### Pattern: Parallel Index With Bridge Dict

**What:** A secondary index (lowercase trie) that maps back to the primary index (original-case label dicts) through a bridge dict (`_lowercase_to_original`).

**Why this pattern:** The existing label-to-index dicts are the source of truth for resolving labels to `OWLClass` objects. Rather than duplicating this resolution logic, the lowercase trie feeds back into the same dicts. One resolution path, two entry points.

```
                 case_sensitive=True                    case_sensitive=False
                       |                                       |
                _label_trie                          _lowercase_label_trie
                       |                                       |
                  original key                          lowercase key
                       |                                       |
                       |                          _lowercase_to_original
                       |                                       |
                       +------- original key(s) ---------------+
                                       |
                          label_to_index / alt_label_to_index
                                       |
                                  List[int] indices
                                       |
                                  self.classes[idx]
                                       |
                                    OWLClass
```

### Pattern: Normalize-on-Entry for Cache

**What:** Normalize the cache key at the entry point of the method, before any logic runs. All downstream code uses the normalized key.

**Why:** Prevents cache fragmentation. If normalization happens inconsistently (sometimes before cache check, sometimes after), you get duplicate entries.

```python
# Correct: normalize once, use everywhere
effective_prefix = prefix.lower() if not case_sensitive else prefix
if effective_prefix in cache:
    return cache[effective_prefix]
# ... compute ...
cache[effective_prefix] = result
```

---

## Anti-Patterns to Avoid

### Anti-Pattern: Lowercasing the Existing Dicts

**What:** Making `label_to_index` store lowercase keys instead of original-case.

**Why bad:** Destroys original case information. `get_by_label("Securities Fraud")` would break. The existing dicts serve multiple purposes beyond prefix search.

### Anti-Pattern: Building Lowercase Trie From Indices Directly

**What:** Having `_lowercase_label_trie` store `(lowercase_key, index)` pairs via `RecordTrie`, bypassing `label_to_index`/`alt_label_to_index` entirely.

**Why bad:** Creates a parallel resolution path. Bugs where one path returns different results than the other. More code, more maintenance, no performance benefit at 18K scale.

### Anti-Pattern: Shared Cache With Type-Switching

**What:** One `_prefix_cache` dict storing both case-sensitive and case-insensitive results, using heuristics to decide which was stored.

**Why bad:** Impossible to distinguish `_prefix_cache["dui"]` as a case-sensitive search for the literal "dui" vs a case-insensitive search that was normalized. Two caches, clearly separated, are unambiguous.

---

## Deduplication Concern

When case-insensitive searching, the same `OWLClass` may be reachable through multiple paths:
- "Securities Fraud" (via `label_to_index`) and "securities fraud" (via `_lowercase_to_original` -> "Securities Fraud" -> same dict)
- An OWLClass whose `label` and `preferred_label` both start with the prefix

The existing `search_by_prefix` does NOT deduplicate -- it can return the same OWLClass multiple times if the same class is indexed under both `label_to_index` and `alt_label_to_index`. This is pre-existing behavior. The new case-insensitive path should add deduplication (using a `seen` set on indices) because the probability of duplicates increases when multiple original-case keys map to the same lowercase key. This is a net improvement.

---

## Memory Impact

| Structure | Estimated Size | Notes |
|-----------|---------------|-------|
| `_lowercase_label_trie` | ~200-400 KB | Same order as existing trie (~18K labels, MARISA is highly compressed) |
| `_lowercase_to_original` | ~1-2 MB | 18K entries, each a list of 1-2 strings |
| `_ci_prefix_cache` | Grows with usage | Same growth pattern as existing cache |

Total additional memory: ~2-3 MB. Negligible for a library that already holds the full FOLIO ontology in memory.

---

## Build Order Implications for Implementation

1. **First:** Add the three new attributes to `__init__` (safe, no behavioral change)
2. **Second:** Build `_lowercase_to_original` and `_lowercase_label_trie` in `parse_owl()` (safe, existing behavior unchanged since `search_by_prefix` doesn't use them yet)
3. **Third:** Modify `search_by_prefix()` to accept `case_sensitive` parameter and branch (behavioral change, but default `False` is the desired new behavior)
4. **Fourth:** Update pure-Python fallback to also support case-insensitive search
5. **Fifth:** Add cache clearing in `parse_owl()` for both caches
6. **Sixth:** Add deduplication to result assembly
7. **Last:** Tests

Steps 1-2 can be done together. Steps 3-6 can be done together. Tests come after the implementation is complete.

---

## Sources

- [marisa-trie documentation](https://marisa-trie.readthedocs.io/en/latest/tutorial.html) -- confirmed `Trie` is key-only, `keys(prefix)` returns all keys with given prefix
- [marisa-trie GitHub](https://github.com/pytries/marisa-trie) -- confirmed API stability
- [marisa-trie PyPI](https://pypi.org/project/marisa-trie/) -- current version info
- Source analysis of `folio/graph.py` lines 160-240, 740-773, 1004-1012, 1134-1167, 1250-1287, 1289-1333
