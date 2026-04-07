# Phase 1: Data Structure Declarations — Plan 1

**Created:** 2026-04-07
**Status:** Complete

## Goal
Declare three new attributes on FOLIOGraph for the parallel lowercase trie, bridge mapping dict, and case-insensitive prefix cache.

## Tasks
1. Add `_lowercase_label_trie: Optional[marisa_trie.Trie] = None` after `_label_trie`
2. Add `_lowercase_to_original: Dict[str, List[str]] = {}` after the lowercase trie
3. Add `_ci_prefix_cache: Dict[str, List[OWLClass]] = {}` after `_prefix_cache`

## Files Modified
- `folio/graph.py` — lines 217-220 (attribute declarations in `__init__`)

## Verification
- All 27 existing tests pass
- Zero behavioral change
