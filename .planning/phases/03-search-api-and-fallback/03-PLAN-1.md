# Phase 3: Search API and Fallback — Plan 1

**Created:** 2026-04-07
**Status:** Complete

## Goal
Wire case-insensitive search through both trie and pure-Python paths with proper deduplication.

## Tasks
1. Add `case_sensitive: bool = False` parameter to `search_by_prefix()`
2. Split into `_search_by_prefix_sensitive()` (original behavior) and `_search_by_prefix_insensitive()` (new)
3. Insensitive path: query `_lowercase_label_trie` with `prefix.casefold()`, resolve through bridge dict
4. Insensitive path: deduplicate results by IRI index using `seen` set
5. Insensitive path: sort original keys by length after bridge dict expansion
6. Pure-Python fallback: apply `casefold()` to both prefix and labels
7. Separate caches: `_prefix_cache` for CS, `_ci_prefix_cache` for CI (keyed by `prefix.casefold()`)

## Files Modified
- `folio/graph.py` — replaced `search_by_prefix()` with three methods

## Verification
- `search_by_prefix("securit")` → 31 results (was 0)
- `search_by_prefix("dui")` → 2 results (was 0)
- `case_sensitive=True` preserves original behavior
- 0 duplicates in CI results
- Existing test_search_prefix needs update in Phase 4 (default changed to CI)
