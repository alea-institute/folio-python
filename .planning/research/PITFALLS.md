# Domain Pitfalls

**Domain:** Case-insensitive prefix search on a parallel lowercase marisa-trie (folio-python)
**Researched:** 2026-04-07

## Critical Pitfalls

Mistakes that cause incorrect results, silent data loss, or require rewrites.

### Pitfall 1: Lowercase Label Collision Produces Duplicate OWLClass Results

**What goes wrong:** Multiple original labels map to the same lowercase key. For example, if both `"DUI"` (an all-caps acronym in `alt_label_to_index`) and `"Dui"` (hypothetical title-case variant in `label_to_index`) both lowercase to `"dui"`, the lowercase trie contains only one key `"dui"`, but the reverse lookup dictionary `lowercase_to_original_labels` must map it to *both* originals. Each original then resolves to its own index list via `label_to_index` or `alt_label_to_index`. If the same OWLClass appears under both labels, `iri_list` will contain that index twice and the caller gets duplicate OWLClass objects in the result.

**Why it happens:** The current `search_by_prefix()` already has no deduplication -- it extends `iri_list` from both `label_to_index` and `alt_label_to_index` without checking for duplicates (lines 1322-1326). Today this is masked because case-sensitive keys rarely collide. Once lowercase keys are introduced, collisions become common.

**Real FOLIO examples from the issue:**
- The maintainer (@mjbommar) explicitly flagged `"turkey" vs "Turkey"` and `"may" vs "May"` as cases where the same lowercase form maps to semantically different concepts (the country vs the bird, the month vs the modal verb). These are not duplicates -- they are *distinct concepts that share a lowercase form*.
- `"US+GA"` (Georgia the U.S. state) and a hypothetical `"Georgia"` (the country) could share the prefix `"georgia"`.

**Consequences:** Callers receive the same OWLClass multiple times in results, inflating result counts and breaking downstream logic that assumes unique results (e.g., folio-mapper selecting top-N candidates).

**Prevention:**
1. Add IRI-based deduplication in `search_by_prefix()` using a `seen_iris: set` -- exactly as `search_by_label()` already does at line 1401-1410.
2. Build the `lowercase_to_original_labels` mapping as `Dict[str, List[str]]` (one lowercase key maps to multiple original labels), then look up ALL originals and extend `iri_list` from each.
3. Deduplicate `iri_list` while preserving order (use `dict.fromkeys(iri_list)` or a seen-set loop).

**Detection:** Write a test that searches for a prefix known to match both a `label` and an `alt_label` of the *same* OWLClass, and assert `len(results) == len(set(r.iri for r in results))`.

**Phase:** Must be addressed in the core implementation phase, not deferred to testing.

---

### Pitfall 2: Reverse Mapping From Lowercase Keys Back to Original Labels is Incomplete

**What goes wrong:** The lowercase trie finds matching lowercase keys, but you still need to look up the original-case labels to resolve indices from `label_to_index` and `alt_label_to_index`. If the reverse mapping (`lowercase -> [original_labels]`) is built incorrectly -- for instance, by overwriting instead of appending when two originals share a lowercase form -- some original labels are silently lost, and their OWLClass objects never appear in results.

**Why it happens:** The natural instinct is `lower_to_original[label.lower()] = label`, which overwrites. The correct structure is `lower_to_original[label.lower()].append(label)` using a `defaultdict(list)` or equivalent.

**Consequences:** Silent result loss -- the exact bug this feature is meant to fix, just in a different form.

**Prevention:**
1. Use `defaultdict(list)` for the reverse mapping.
2. Populate it from *both* `label_to_index.keys()` and `alt_label_to_index.keys()`.
3. Write a test asserting that `len(lower_to_original_labels)` is <= total unique labels (proving many-to-one mapping works), AND that resolving any lowercase key back through the mapping reaches all the original labels.

**Detection:** After building the mapping, assert `sum(len(v) for v in lower_to_original.values()) == len(all_labels)`. If less, labels were dropped.

**Phase:** Core implementation phase -- this is the data structure design, not an afterthought.

---

### Pitfall 3: Cache Serves Stale or Split Results When Mixing Case Modes

**What goes wrong:** The current `_prefix_cache` is a plain `Dict[str, List[OWLClass]]` keyed by the raw prefix string (line 1300). If `case_sensitive` becomes a parameter:
- `search_by_prefix("Securit", case_sensitive=True)` caches under key `"Securit"` with 39 results.
- `search_by_prefix("Securit", case_sensitive=False)` hits the *same cache key* `"Securit"` and returns the case-sensitive results (39 instead of potentially more).
- Conversely, `search_by_prefix("securit", case_sensitive=False)` caches under `"securit"`, and a later `search_by_prefix("securit", case_sensitive=True)` returns the case-insensitive results (wrong -- case-sensitive search for `"securit"` should return 0).

**Why it happens:** The cache key does not encode the `case_sensitive` flag.

**Consequences:** Incorrect search results that depend on call order -- a heisenbug that's nearly impossible to reproduce reliably in testing but causes production failures.

**Prevention:** Two options (pick one):
1. **Separate caches:** `_prefix_cache_cs` and `_prefix_cache_ci` -- simple, no ambiguity.
2. **Compound cache key:** `_prefix_cache[(prefix, case_sensitive)]` -- single dict, but requires changing the key type.

Option 1 is cleaner because case-insensitive cache can normalize the prefix to lowercase before lookup (`_prefix_cache_ci[prefix.lower()]`), ensuring `"Securit"` and `"securit"` share one cache entry when case-insensitive.

**Detection:** Write a test that calls `search_by_prefix("Securit", case_sensitive=True)` then `search_by_prefix("Securit", case_sensitive=False)` and asserts the second call returns a superset of the first.

**Phase:** Core implementation phase -- cache design must match the API contract from the start.

---

### Pitfall 4: `refresh()` Does Not Clear the New Lowercase Trie or Cache

**What goes wrong:** The existing `refresh()` method (lines 1257-1266) clears `label_to_index`, `alt_label_to_index`, `class_edges`, and `triples`, but it does NOT clear `_prefix_cache` or `_label_trie`. After `refresh()`, the trie and cache contain stale entries pointing to old indices that no longer exist in `self.classes`. This is an *existing bug* that will be inherited by the new lowercase trie and its reverse mapping.

**Why it happens:** `refresh()` was written before the trie/cache were added, or the clearing was simply missed.

**Consequences:** After `refresh()`, prefix searches return stale results or raise `IndexError` when materializing `self[index]` for an index that no longer exists.

**Prevention:**
1. Fix `refresh()` to also clear `_label_trie`, the new `_lowercase_label_trie`, `_prefix_cache` (both case-sensitive and case-insensitive variants), and `_lower_to_original_labels`.
2. Alternatively, since `refresh()` calls `parse_owl()` which rebuilds the trie at lines 1004-1012, the trie itself gets rebuilt -- but the *cache* is definitely stale and must be cleared.
3. Add a `_clear_search_indices()` helper that `refresh()` and `__init__` both call.

**Detection:** Write a test: call `search_by_prefix("Mich")`, then `refresh()`, then `search_by_prefix("Mich")` again, and assert the second result is fresh (same content but re-materialized from new indices).

**Phase:** Should be fixed as part of the implementation phase since you are already modifying the search infrastructure.

---

## Moderate Pitfalls

### Pitfall 5: Using `str.lower()` Instead of `str.casefold()` for Normalization

**What goes wrong:** Python's `str.lower()` is locale-unaware and does not handle certain Unicode case mappings. The classic example is the German Eszett: `"STRASSE".lower()` produces `"strasse"`, but `"Stra\u00dfe".casefold()` produces `"strasse"` while `"Stra\u00dfe".lower()` produces `"stra\u00dfe"` -- these do not match.

**Why it matters for FOLIO:** The PROJECT.md states "no evidence of non-ASCII labels in FOLIO" and declares Unicode normalization beyond `.lower()` as out of scope. This is a *reasonable scoping decision* for now, because FOLIO labels are English legal terms. However, FOLIO includes labels for international jurisdictions (Denmark/DK, Georgia), and future ontology versions may add non-ASCII labels (e.g., German legal terms like "Gesch\u00e4ftsf\u00fchrer" or French "Soci\u00e9t\u00e9").

**Prevention:**
1. Use `str.casefold()` instead of `str.lower()` -- it costs nothing extra and is the Python-recommended approach for case-insensitive comparison.
2. Both the trie keys AND the query prefix must use the same normalization (`prefix.casefold()` and `label.casefold()`).
3. Document the normalization choice so future contributors know what to expect.

**Detection:** `"stra\u00dfe".casefold() == "strasse".casefold()` returns `True`; `"stra\u00dfe".lower() == "strasse".lower()` returns `False`.

**Note:** The maintainer's comment about "turkey vs Turkey" is about *semantic* distinction (country vs bird), NOT about Unicode edge cases. `str.casefold()` would not help distinguish those -- that requires the `case_sensitive=True` parameter.

---

### Pitfall 6: Pure-Python Fallback Path Diverges From Trie Path

**What goes wrong:** The existing code has two code paths: one using `marisa_trie` (lines 1304-1309) and one using pure Python list comprehension (lines 1311-1320). Both must be updated for case-insensitive search. If only the trie path is updated, users without `marisa_trie` installed get different (case-sensitive) behavior -- a silent behavioral divergence.

**Why it happens:** The fallback path is easy to forget because it is only exercised when `marisa_trie` is not installed, and the test suite almost certainly runs with it installed.

**Consequences:** Bug reports from users who install `folio-python` without the search extras, or in constrained environments where C extensions cannot be compiled.

**Prevention:**
1. Update *both* paths in the same commit/PR.
2. The pure-Python fallback for case-insensitive search is: `[label for label in all_labels if label.lower().startswith(prefix.lower())]` (or `.casefold()`).
3. Add a test that monkeypatches `marisa_trie` to `None` and verifies case-insensitive search still works.

**Detection:** In tests, use `@pytest.fixture` to temporarily set the module-level `marisa_trie` to `None` and run the same search assertions.

**Phase:** Core implementation phase -- both paths must be updated simultaneously.

---

### Pitfall 7: The `case_sensitive=False` Default Silently Changes Existing Behavior

**What goes wrong:** If `case_sensitive` defaults to `False`, existing callers who pass title-cased prefixes (e.g., `search_by_prefix("Mich")`) will now receive a *superset* of previous results -- their existing matches plus any additional matches from other case variants. This is the intended behavior per PROJECT.md ("returns a superset"), but it can break tests or downstream code that asserts exact result counts or exact ordering.

**Why it happens:** A default-False parameter is an API-compatible change in *contract* (superset of old results), but not in *exact output* (more results, possibly different order).

**Consequences:**
- The existing test `test_search_prefix` (line 256-259) searches for `"Mich"` and asserts the first result's label is `"Michigan"`. This might still pass if "Michigan" remains first in sort order, but the result count changes.
- Benchmark test `test_benchmark_search_prefix` (line 455-458) measures performance; more results may change timing characteristics.

**Prevention:**
1. Verify the existing test still passes with the new default by running the full test suite after implementation.
2. If the superset guarantee is important, add an explicit test: `assert set(case_insensitive_results) >= set(case_sensitive_results)`.
3. Consider whether the sorted-by-length ordering (line 1306-1308) still produces intuitive results when case variants are merged.

**Detection:** Run `pytest tests/test_folio.py::test_search_prefix -v` before and after the change.

**Phase:** Testing phase, but must be anticipated during implementation design.

---

### Pitfall 8: Trie Key Length Filter Drops Short Acronyms

**What goes wrong:** The trie building code (line 1010) filters out labels shorter than `MIN_PREFIX_LENGTH` (which is 3, per line 125). This means two-character labels like `"IP"`, `"DK"`, or `"EU"` are never inserted into the trie and cannot be found by prefix search. The same filter will apply to the lowercase trie.

**Why it matters:** The issue explicitly calls out `"ip"` as a case where case-insensitive search should match `"IP Licensing"`. The prefix `"ip"` is only 2 characters, so `search_by_prefix("ip")` would fail regardless of case -- not because of case sensitivity, but because of the length filter. Users will think case-insensitive search is broken when it is actually a different issue.

**Consequences:** Confusion and bug reports. The case-insensitive feature appears not to work for short prefixes.

**Prevention:**
1. Document in the `search_by_prefix()` docstring that prefixes shorter than `MIN_PREFIX_LENGTH` (3) may not match.
2. Consider whether `MIN_PREFIX_LENGTH` should be lowered to 2 for the lowercase trie (this is a separate decision from case-insensitivity).
3. Ensure the new tests do not test 2-character prefixes and then blame case-insensitivity for the failure.

**Detection:** `search_by_prefix("IP")` returns `[]` even today. Verify this is documented.

**Phase:** Scoping/design phase -- decide whether to address this or explicitly mark out of scope.

---

## Minor Pitfalls

### Pitfall 9: The Turkish I Problem is Irrelevant but Will Be Raised

**What goes wrong:** Someone reviewing the code will point out that `"INFO".lower()` produces `"info"` in Python (correct) but would produce `"i\u0307nfo"` in a Turkish locale. In Python 3, `str.lower()` and `str.casefold()` are NOT locale-dependent -- they always use Unicode default case mappings. The Turkish I problem affects C's `tolower()` and Java's `String.toLowerCase(Locale)`, but NOT Python 3 strings.

**Why it matters:** This is a non-issue for Python, but it will waste review time if not preemptively addressed.

**Prevention:** Add a code comment: `# Python 3's str.lower()/casefold() uses Unicode default mapping, not locale-dependent. Turkish I is not an issue.`

**Detection:** `"\u0130".casefold() == "i\u0307"` in Python 3 (always, regardless of locale).

---

### Pitfall 10: Memory Doubling Concern is a Red Herring

**What goes wrong:** A reviewer flags that building a second marisa-trie doubles memory usage for the trie. Since the project has approximately 18K concepts and `marisa-trie` is a compressed LOUDS-based structure, the entire trie fits in hundreds of KB. The reverse mapping `Dict[str, List[str]]` is similarly small.

**Why it matters:** This is a non-issue but will be raised.

**Prevention:** The maintainer already approved this approach in the issue comments: "It's cheap because the data structure is so cheap to keep in memory and efficient for lookup."

---

### Pitfall 11: Labels With Special Characters Lowercase Identically

**What goes wrong:** Labels like `"M&A Practice Components"` contain special characters. `"M&A".lower()` produces `"m&a"`, which is fine. But consider `"M&A"` vs `"M&a"` vs `"m&A"` -- all lowercase to `"m&a"`. If these are distinct labels in the ontology (unlikely but possible), they share one lowercase trie entry. This is by design, but worth being aware of.

**Prevention:** The reverse mapping handles this naturally if built as `Dict[str, List[str]]`. No special handling needed for `&`, `-`, `.`, or other non-alpha characters since `.lower()` and `.casefold()` pass them through unchanged.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Data structure design | Pitfall 2 (reverse mapping) | Use `defaultdict(list)`, populate from both label dicts |
| Trie building | Pitfall 8 (MIN_PREFIX_LENGTH) | Document the 3-char minimum, decide scope |
| search_by_prefix() rewrite | Pitfall 1 (duplicates), Pitfall 3 (cache) | Add IRI dedup, separate caches per mode |
| Pure-Python fallback | Pitfall 6 (divergence) | Update both paths simultaneously |
| refresh() integration | Pitfall 4 (stale cache) | Clear all new data structures in refresh() |
| Test writing | Pitfall 7 (default change) | Test superset property, not exact counts |
| Normalization choice | Pitfall 5 (lower vs casefold) | Use casefold() everywhere, consistently |
| Code review | Pitfall 9 (Turkish I), Pitfall 10 (memory) | Preemptive comments addressing non-issues |

## Sources

- [marisa-trie tutorial and API docs](https://marisa-trie.readthedocs.io/en/latest/tutorial.html) - Trie key behavior, duplicate handling
- [marisa-trie GitHub](https://github.com/pytries/marisa-trie) - Source code and issue tracker
- [Python `str.casefold()` vs `str.lower()`](https://dev.to/bowmanjd/case-insensitive-string-comparison-in-python-using-casefold-not-lower-5fpi) - Best practice for case-insensitive comparison
- [Python bug tracker: Turkish I](https://bugs.python.org/issue34723) - `lower()` on Turkish I returns 2-char string
- [GitHub Issue #15](https://github.com/alea-institute/folio-python/issues/15) - Original feature request with edge cases
- [Maintainer comment on Issue #15](https://github.com/alea-institute/folio-python/issues/15#issuecomment) - Approval of Option 1, flags "turkey vs Turkey" and "may vs May"
- [hat-trie case-insensitive prefix search discussion](https://github.com/Tessil/hat-trie/issues/7) - General trie case-insensitivity patterns
- Current source code analysis: `folio/graph.py` lines 125, 200-218, 740-773, 1004-1012, 1250-1333
