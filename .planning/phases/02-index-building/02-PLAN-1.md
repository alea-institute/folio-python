# Phase 2: Index Building — Plan 1

**Created:** 2026-04-07
**Status:** Complete

## Goal
Build the parallel lowercase trie and bridge dict during parse_owl(), and fix pre-existing cache staleness on refresh().

## Tasks
1. Clear both `_prefix_cache` and `_ci_prefix_cache` at start of trie-building block (fixes refresh() staleness)
2. Build `_lowercase_to_original` dict mapping `label.casefold()` → `[original_labels]` from all labels meeting MIN_PREFIX_LENGTH
3. Build `_lowercase_label_trie` from `_lowercase_to_original.keys()`

## Files Modified
- `folio/graph.py` — trie-building block in `parse_owl()` (after line 1005)

## Verification
- All 27 existing tests pass
- Zero behavioral change (new structures populated but not yet queried)
