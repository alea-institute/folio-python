# Feature Landscape: Case-Insensitive Prefix Search

**Domain:** Ontology label prefix search / autocomplete
**Researched:** 2026-04-07

## Table Stakes

Features that every prefix search / autocomplete implementation handles. Missing any of these would be surprising to callers.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `case_sensitive` parameter | Elasticsearch added this as a query-time flag (issue #61546). Whoosh defaults to case-insensitive. fast-autocomplete docs explicitly tell users to lowercase everything. Every mature search system supports this toggle. | Low | Boolean parameter, default `False`. The ecosystem consensus is overwhelming: case-insensitive is the default behavior for search. |
| Lowercase normalization at index time | The standard pattern across marisa-trie, fast-autocomplete, pygtrie, and SQLite FTS5: build a parallel normalized index. marisa-trie has no built-in case folding -- you must normalize keys before insertion. | Low | Build a second `marisa_trie.Trie` with `.lower()` keys alongside the existing case-preserving trie. ~18K concepts means negligible memory cost. |
| Lowercase normalization at query time | Complement to index-time normalization. The query prefix must be lowered with the same function used at index time. | Low | `prefix.lower()` before trie lookup when `case_sensitive=False`. |
| Reverse mapping from normalized to original | When the trie stores lowercase keys, results must map back to original-case labels to retrieve the correct `OWLClass` objects. fast-autocomplete sidesteps this by requiring callers to lowercase everything; folio-python must preserve original labels. | Low-Med | A `Dict[str, List[str]]` mapping `lowercase_label -> [original_label_1, ...]`. Built once during `_load_folio()`. |
| Cache normalization | Prefix cache must not store separate entries for "securit", "Securit", "SECURIT" when case-insensitive. The cache key should be the normalized (lowered) prefix. | Low | Normalize cache key to `.lower()` when `case_sensitive=False`. Existing `_prefix_cache` dict keyed by raw prefix string, so this is a minor conditional. |
| Pure-Python fallback parity | The existing code has both a marisa-trie path and a pure-Python `startswith()` fallback. Both paths must support case-insensitive search identically. | Low | Add `.lower()` to the `startswith()` comparison in the fallback path. |

## Differentiators

Features that go beyond the baseline. Not expected for this scope, but could add value in the future.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `str.casefold()` instead of `str.lower()` | Handles Unicode edge cases like German sharp-s (ss/ss), Greek sigma variants, Turkic dotted-I. Python docs recommend `casefold()` for "caseless matching." However, FOLIO ontology labels are English-language legal terms -- no evidence of non-ASCII labels exists in the ~18K concepts. | Low | One-line change from `.lower()` to `.casefold()`. Almost zero risk. **Recommendation: use `casefold()` anyway** -- it costs nothing and is the Python-idiomatic choice for case-insensitive comparison. If FOLIO ever adds non-English labels, it works correctly out of the box. |
| Unicode NFKD normalization + accent stripping | Decomposes accented characters (e.g., "Munchen" matches "Muenchen") using `unicodedata.normalize('NFKD')` + filtering combining marks. SQLite FTS5's unicode61 tokenizer does this by default. | Medium | Requires building a third normalized trie or a normalization pipeline. Overkill for FOLIO's English-only legal taxonomy. Accent stripping can destroy meaning in languages where accents are phonemically significant. |
| Locale-aware case folding | Python's `casefold()` follows Unicode's default case folding rules, but some languages have locale-specific rules (e.g., Turkish I/I). ICU-based folding via `icu` or `pyicu` handles these correctly. | High | Adds a C library dependency (libicu). Completely unnecessary for English legal taxonomy labels. |
| Typo tolerance / fuzzy prefix matching | fast-autocomplete supports Levenshtein distance (`max_cost` parameter). Elasticsearch offers fuzzy prefix queries. Combines prefix matching with edit distance. | High | Already partially covered by `search_by_label()` which uses rapidfuzz for fuzzy matching. Adding fuzzy logic to prefix search would blur the distinction between the two methods. |
| Result ranking / scoring | fast-autocomplete ranks by configurable count values. Elasticsearch ranks by relevance score. Current `search_by_prefix()` sorts by label length (shortest first), which is a reasonable proxy for relevance in a prefix search context. | Medium | Not needed for the current use case -- callers want all matches for a prefix, sorted by specificity (length). |
| Synonym expansion during prefix search | fast-autocomplete supports clean synonyms and partial synonyms. FOLIO already stores alternative labels (`alt_label_to_index`) which serve as synonyms. | Medium | Already implemented via alt_label inclusion in the trie. No additional synonym infrastructure needed. |
| Hidden labels for search only | SKOS defines `hiddenLabel` for terms that should match during search but never display to users (common misspellings, deprecated names). | Medium | Would require extending `OWLClass` model and parser. Not needed for this milestone. |

## Anti-Features

Features to explicitly NOT build for this scope.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full-text / substring search | Prefix search is O(prefix length) in a trie. Substring search requires fundamentally different data structures (suffix trees, n-gram indexes, FTS). Mixing concerns would complicate the API and confuse callers about performance characteristics. | Keep `search_by_prefix()` for prefix matching. Use `search_by_label()` (rapidfuzz) for fuzzy/substring-like matching. |
| Configurable normalization pipeline | Over-engineering. A pluggable normalizer (lowercase -> casefold -> NFKD -> accent strip -> ...) adds API surface and testing burden for zero current benefit. | Hardcode `casefold()` normalization. Revisit if FOLIO adds non-English labels. |
| Regex-based prefix matching | Python's `re` module supports case-insensitive matching, but regex prefix search cannot use the trie's O(prefix) lookup. It would require scanning all labels -- defeating the purpose of having a trie. | Use the trie for prefix matching, regex for other use cases. |
| Automatic case detection | Some systems infer case sensitivity from the query (e.g., "if query has uppercase, search case-sensitively"). This is fragile, surprising, and makes behavior depend on input rather than explicit configuration. Whoosh mentions this pattern but it creates unpredictable UX. | Use an explicit `case_sensitive` parameter. Predictable beats clever. |
| N-gram / edge-ngram indexing | Elasticsearch uses edge-ngram tokenizers for autocomplete at scale. This is a heavyweight indexing strategy for millions of documents. FOLIO has ~18K concepts -- a second trie is sufficient and far simpler. | Parallel lowercase trie. |
| Removing the existing case-sensitive trie | Backward compatibility. Existing callers may depend on exact-case behavior. | Preserve via `case_sensitive=True` parameter. Both tries coexist. |

## Feature Dependencies

```
case_sensitive parameter
  -> lowercase normalization at index time (needs the lowercase trie to exist)
  -> lowercase normalization at query time (needs to match index normalization)
  -> reverse mapping normalized -> original (needs to resolve OWLClass from lowercase keys)

cache normalization
  -> case_sensitive parameter (cache key strategy depends on mode)

pure-Python fallback parity
  -> case_sensitive parameter (same parameter controls both paths)
```

All table-stakes features form a single dependency chain rooted in the `case_sensitive` parameter. They should be implemented as one atomic unit, not incrementally.

## MVP Recommendation

**Implement all table-stakes features as a single unit.** They are interdependent and individually incomplete.

Prioritize:
1. **Parallel lowercase trie** built during `_load_folio()` using `str.casefold()` (not `str.lower()`)
2. **`case_sensitive=False` default** on `search_by_prefix()`
3. **Reverse mapping dict** (`casefold_label -> [original_labels]`) for OWLClass resolution
4. **Cache key normalization** to `casefold()` when case-insensitive
5. **Pure-Python fallback** updated with same `casefold()` logic
6. **Tests** covering: lowercase input, UPPERCASE input, mixed case, acronyms (DUI), symbols (M&A), pure-Python fallback path

**Use `casefold()` over `lower()`** -- it is the Python-recommended approach for caseless comparison, costs nothing extra, and future-proofs against non-ASCII labels.

Defer:
- **Unicode NFKD normalization**: No evidence of accented characters in FOLIO labels. Revisit if FOLIO internationalization happens.
- **Locale-aware folding**: Would add a C dependency (libicu) for zero current benefit.
- **Fuzzy prefix search**: Already covered by `search_by_label()` via rapidfuzz.

## Sources

- [marisa-trie documentation](https://marisa-trie.readthedocs.io/en/latest/tutorial.html) -- confirms no built-in case folding; normalization must happen before insertion
- [fast-autocomplete PyPI](https://pypi.org/project/fast-autocomplete/) -- case-sensitive by default, recommends lowercasing before insertion
- [Elasticsearch case_insensitive flag (issue #61546)](https://github.com/elastic/elasticsearch/issues/61546) -- added `case_insensitive` parameter to prefix queries
- [Whoosh documentation](https://whoosh.readthedocs.io/en/latest/recipes.html) -- defaults to case-insensitive via LowercaseFilter in analyzer
- [pygtrie (Google)](https://github.com/google/pygtrie) -- no built-in case normalization; key normalization is caller's responsibility
- [SQLite FTS5 documentation](https://www.sqlite.org/fts5.html) -- unicode61 tokenizer provides case folding and optional diacritic removal by default
- [Python str.casefold() vs str.lower()](https://docs.vultr.com/python/standard-library/str/casefold) -- casefold() handles Unicode edge cases (sharp-s, Greek sigma)
- [OpenSearch Autocomplete documentation](https://docs.opensearch.org/latest/search-plugins/searching-data/autocomplete/) -- edge-ngram and completion suggester approaches
- [Python unicodedata.normalize](https://docs.python.org/3/library/unicodedata.html) -- NFKD decomposition for accent stripping
- [SKOS Reference (W3C)](https://www.w3.org/TR/skos-reference/) -- hiddenLabel for search-only terms
