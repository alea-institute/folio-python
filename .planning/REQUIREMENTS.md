# Requirements: Case-Insensitive Prefix Search

**Defined:** 2026-04-07
**Core Value:** Prefix search must return correct results regardless of input casing

## v1 Requirements

### Data Structures

- [ ] **DS-01**: FOLIOGraph declares `_lowercase_label_trie` attribute (parallel `marisa_trie.Trie` with casefolded keys)
- [ ] **DS-02**: FOLIOGraph declares `_lowercase_to_original` attribute (`Dict[str, List[str]]` mapping casefolded labels to original-case labels)
- [ ] **DS-03**: FOLIOGraph declares `_ci_prefix_cache` attribute (separate cache for case-insensitive queries)

### Index Building

- [ ] **IDX-01**: `parse_owl()` builds `_lowercase_to_original` dict using `defaultdict(list)` from both `label_to_index` and `alt_label_to_index` keys with `casefold()`
- [ ] **IDX-02**: `parse_owl()` builds `_lowercase_label_trie` from `_lowercase_to_original.keys()` (deduplicated by construction)
- [ ] **IDX-03**: `parse_owl()` clears `_prefix_cache` and `_ci_prefix_cache` at start of trie-building block (fixes pre-existing `refresh()` staleness)

### Search API

- [ ] **API-01**: `search_by_prefix()` accepts `case_sensitive: bool = False` parameter
- [ ] **API-02**: When `case_sensitive=False`, queries the lowercase trie with `prefix.casefold()`
- [ ] **API-03**: When `case_sensitive=True`, queries the existing trie with original prefix (preserves backward compat)
- [ ] **API-04**: Case-insensitive results resolve through bridge dict → `label_to_index`/`alt_label_to_index` → `OWLClass`
- [ ] **API-05**: Results are deduplicated by IRI index using a `seen` set (prevents duplicates from lowercase collisions)
- [ ] **API-06**: Case-insensitive queries use `_ci_prefix_cache` keyed by `prefix.casefold()`

### Fallback Parity

- [ ] **FB-01**: Pure-Python fallback path (when `marisa_trie` is not installed) supports `case_sensitive` parameter
- [ ] **FB-02**: Pure-Python fallback applies `casefold()` to both query prefix and labels when `case_sensitive=False`

### Tests

- [ ] **TEST-01**: Test case-insensitive search returns results for lowercase input (e.g., `"securit"` matches "Securities Fraud")
- [ ] **TEST-02**: Test case-insensitive search handles acronyms (e.g., `"dui"` matches "DUI")
- [ ] **TEST-03**: Test `case_sensitive=True` preserves original behavior (e.g., `"securit"` returns nothing, `"Securit"` returns results)
- [ ] **TEST-04**: Test no duplicate OWLClass objects in results
- [ ] **TEST-05**: Test existing `test_search_prefix` still passes (backward compat — "Mich" result ordering)
- [ ] **TEST-06**: Test pure-Python fallback produces same results as trie path

## v2 Requirements

### Extended Normalization

- **NORM-01**: NFKD Unicode normalization for non-ASCII labels
- **NORM-02**: Accent/diacritic stripping for broader matching

### Prefix Length

- **LEN-01**: Lower `MIN_PREFIX_LENGTH` to 2 for short acronyms ("IP", "DK", "EU")

## Out of Scope

| Feature | Reason |
|---------|--------|
| Locale-aware case folding | Python 3 `casefold()` is sufficient; FOLIO labels are English |
| Fuzzy prefix matching | `search_by_label()` already covers fuzzy via rapidfuzz |
| Changing `search_by_label()` | Already case-insensitive |
| Removing case-sensitive trie | Preserved via `case_sensitive=True` parameter |
| `MIN_PREFIX_LENGTH` change | Separate concern, keep at 3 for this PR |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DS-01 | Phase 1 | Pending |
| DS-02 | Phase 1 | Pending |
| DS-03 | Phase 1 | Pending |
| IDX-01 | Phase 2 | Pending |
| IDX-02 | Phase 2 | Pending |
| IDX-03 | Phase 2 | Pending |
| API-01 | Phase 3 | Pending |
| API-02 | Phase 3 | Pending |
| API-03 | Phase 3 | Pending |
| API-04 | Phase 3 | Pending |
| API-05 | Phase 3 | Pending |
| API-06 | Phase 3 | Pending |
| FB-01 | Phase 3 | Pending |
| FB-02 | Phase 3 | Pending |
| TEST-01 | Phase 4 | Pending |
| TEST-02 | Phase 4 | Pending |
| TEST-03 | Phase 4 | Pending |
| TEST-04 | Phase 4 | Pending |
| TEST-05 | Phase 4 | Pending |
| TEST-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-04-07*
*Last updated: 2026-04-07 after initial definition*
