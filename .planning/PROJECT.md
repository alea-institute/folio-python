# Case-Insensitive Prefix Search for folio-python

## What This Is

Adding case-insensitive prefix search to the folio-python library's `search_by_prefix()` method. Currently, prefix search is case-sensitive because the underlying `marisa-trie` stores labels in their original case (e.g., "Securities Fraud", "DUI", "M&A Practice Components"), but all realistic callers lowercase their input before searching — causing 100% silent miss rates.

## Core Value

Prefix search must return correct results regardless of input casing — `search_by_prefix("securit")` must match "Securities Fraud" just as `search_by_prefix("Securit")` does today.

## Requirements

### Validated

- Existing case-sensitive `search_by_prefix()` works correctly for exact-case input — existing
- `search_by_label()` already handles case insensitivity via rapidfuzz — existing
- Trie is built from both `label_to_index` and `alt_label_to_index` keys — existing

### Active

- [ ] Build parallel lowercase `marisa-trie` alongside existing case-sensitive trie
- [ ] Add `case_sensitive` parameter to `search_by_prefix()` defaulting to `False`
- [ ] Fix pure-Python fallback path to also support case-insensitive search
- [ ] Normalize prefix cache to share entries across case variants when case-insensitive
- [ ] Map lowercase trie keys back to original `OWLClass` objects correctly
- [ ] Add tests covering case-insensitive prefix search (lowercase, UPPERCASE, mixed, acronyms like "DUI", symbols like "M&A")

### Out of Scope

- Changing `search_by_label()` behavior — already case-insensitive
- Unicode normalization beyond `.lower()` — no evidence of non-ASCII labels in FOLIO
- Removing the existing case-sensitive trie — preserved via `case_sensitive=True` parameter

## Context

- **Upstream issue:** alea-institute/folio-python#15
- **Maintainer approval:** @mjbommar confirmed Option 1 (parallel lowercase trie) in issue comments
- **Impact:** folio-mapper's Area of Law branch returns only 1 candidate instead of 5+ due to this bug
- **Existing workaround:** folio-mapper tries both `.capitalize()` and lowercase, but fails for "DUI", "M&A", "IP" edge cases
- **Library size:** ~18K FOLIO concepts — memory is not a constraint for a second trie
- **Trie location:** `graph.py:1004-1012` builds the trie during `_load_folio()`
- **Search location:** `graph.py:1289-1333` implements `search_by_prefix()`

## Constraints

- **Backward compatibility**: Existing `search_by_prefix("Securit")` must continue to work — the new `case_sensitive=False` default returns a superset of what `case_sensitive=True` would return
- **No new dependencies**: Only uses existing `marisa_trie` (already a dependency)
- **Branch strategy**: Feature branch `feature/case-insensitive-prefix` targeting `main`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Option 1: Parallel lowercase trie | Cheap in memory (~18K concepts), O(prefix) lookup, simple mapping back to OWLClass via lowercase→original label dict | -- Pending |
| `case_sensitive=False` default | Matches user expectation — all realistic callers lowercase input | -- Pending |
| Shared prefix cache (normalized to lowercase) | Avoids duplicate cache entries for "securit" vs "Securit" when case-insensitive | -- Pending |
| Fix both trie and pure-Python fallback | Consistent behavior regardless of whether marisa_trie is installed | -- Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-07 after initialization*
