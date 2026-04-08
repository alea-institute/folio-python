# Phase 4: Test Suite — Plan 1

**Created:** 2026-04-07
**Status:** Complete

## Goal
Validate correctness, backward compatibility, and edge case handling with automated tests.

## Tasks
1. Update existing `test_search_prefix` to use `case_sensitive=True` (preserves original assertion)
2. Add `test_search_prefix_case_insensitive` — lowercase "securit" matches title-case labels
3. Add `test_search_prefix_case_insensitive_acronym` — "dui" matches "DUI"/"Driving Under the Influence"
4. Add `test_search_prefix_case_sensitive_preserves_behavior` — CS=True: "securit"→0, "Securit"→results
5. Add `test_search_prefix_no_duplicates` — no duplicate OWLClass IRIs in CI results
6. Add `test_search_prefix_fallback_parity` — monkeypatch trie to None, verify fallback matches trie results

## Files Modified
- `tests/test_folio.py` — updated 1 test, added 5 new tests

## Verification
- 32 tests pass (up from 27)
- 1 pre-existing error (benchmark fixture not installed) — unrelated
