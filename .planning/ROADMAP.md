# Roadmap: Case-Insensitive Prefix Search

## Overview

This roadmap delivers case-insensitive prefix search for folio-python's `search_by_prefix()` method. The work progresses from declaring new data structures, through building parallel indexes, to modifying search behavior, and finally validating correctness with comprehensive tests. Each phase builds on the previous one, with the first two phases introducing zero behavioral change and Phase 3 delivering the actual feature flip.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Data Structure Declarations** - Declare new attributes on FOLIOGraph for lowercase trie, bridge dict, and CI cache
- [ ] **Phase 2: Index Building** - Build the parallel lowercase trie and bridge dict during parse_owl()
- [ ] **Phase 3: Search API and Fallback** - Wire case-insensitive search through both trie and pure-Python paths
- [ ] **Phase 4: Test Suite** - Validate correctness, backward compatibility, and edge cases

## Phase Details

### Phase 1: Data Structure Declarations
**Goal**: FOLIOGraph has all new attributes declared so subsequent phases can populate and query them
**Depends on**: Nothing (first phase)
**Requirements**: DS-01, DS-02, DS-03
**Success Criteria** (what must be TRUE):
  1. FOLIOGraph instances have a `_lowercase_label_trie` attribute initialized to None or empty
  2. FOLIOGraph instances have a `_lowercase_to_original` dict attribute initialized to empty
  3. FOLIOGraph instances have a `_ci_prefix_cache` dict attribute initialized to empty
  4. Existing tests still pass with no behavioral change
**Plans**: TBD

### Phase 2: Index Building
**Goal**: parse_owl() populates the lowercase trie and bridge dict so they are ready for queries after loading
**Depends on**: Phase 1
**Requirements**: IDX-01, IDX-02, IDX-03
**Success Criteria** (what must be TRUE):
  1. After parse_owl() completes, `_lowercase_to_original` maps every casefolded label/altLabel to its original-case variant(s)
  2. After parse_owl() completes, `_lowercase_label_trie` contains all keys from `_lowercase_to_original`
  3. Both `_prefix_cache` and `_ci_prefix_cache` are cleared at the start of the trie-building block (fixing pre-existing refresh() staleness)
  4. Existing tests still pass with no behavioral change
**Plans**: TBD

### Phase 3: Search API and Fallback
**Goal**: Users can call search_by_prefix() with any casing and get correct results
**Depends on**: Phase 2
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, FB-01, FB-02
**Success Criteria** (what must be TRUE):
  1. `search_by_prefix("securit")` returns results including "Securities Fraud" (lowercase input matches title-case labels)
  2. `search_by_prefix("Securit", case_sensitive=True)` returns the same results as before this change (backward compat)
  3. `search_by_prefix("dui")` returns results including "DUI" (acronym case insensitivity)
  4. No duplicate OWLClass objects appear in any result set
  5. When marisa_trie is not installed, the pure-Python fallback produces equivalent case-insensitive results
**Plans**: TBD

### Phase 4: Test Suite
**Goal**: Automated tests prove correctness, backward compatibility, and edge case handling
**Depends on**: Phase 3
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06
**Success Criteria** (what must be TRUE):
  1. A test asserts lowercase prefix input returns correct OWLClass results (TEST-01)
  2. A test asserts acronym queries like "dui" match their uppercase labels (TEST-02)
  3. A test asserts case_sensitive=True preserves original behavior -- "securit" returns nothing, "Securit" returns results (TEST-03)
  4. A test asserts no duplicate OWLClass objects in results (TEST-04)
  5. The existing `test_search_prefix` ("Mich" ordering) still passes unchanged (TEST-05)
  6. A test asserts pure-Python fallback produces same results as the trie path (TEST-06)
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Structure Declarations | 0/0 | Not started | - |
| 2. Index Building | 0/0 | Not started | - |
| 3. Search API and Fallback | 0/0 | Not started | - |
| 4. Test Suite | 0/0 | Not started | - |
