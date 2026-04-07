# Codebase Concerns

**Analysis Date:** 2026-04-07

## Tech Debt

**Unparsed RDF/OWL Elements:**
- Issue: Four OWL element types are recognized but not parsed: DatatypeProperty, AnnotationProperty, NamedIndividual, and RDF Description
- Files: `folio/graph.py:946-957`
- Impact: Ontology data in these formats is silently skipped. If FOLIO extends to use these constructs, information loss will occur silently.
- Fix approach: Implement parsing for each element type with corresponding model classes and storage structures. Add test cases for each type.

**JSON-LD Translation Bug (Destructive Loop):**
- Issue: In `to_jsonld()` method, translations loop overwrites `skos:altLabel` array on each iteration instead of appending
- Files: `folio/models.py:465-470`
- Impact: Only the last translation is preserved in JSON-LD output; earlier translations are lost. This corrupts the output for multilingual classes.
- Fix approach: Change line 467 from assignment to append check. Initialize the array once outside the loop if not present.

**Incomplete LLM System Prompt:**
- Issue: LLM search uses a hardcoded minimal system prompt without full task definition
- Files: `folio/graph.py:1560-1561`
- Impact: LLM search quality is constrained by insufficient context. Response format may be unpredictable without schema enforcement.
- Fix approach: Expand system prompt to include task context, output format requirements, and confidence scoring guidelines. Implement token caching once alea-llm-client supports it (noted in TODO at line 8).

**Version Mismatch:**
- Issue: Package version in `__init__.py` is "0.2.0" but `pyproject.toml` declares "0.2.1"
- Files: `folio/__init__.py:8`, `pyproject.toml:3`
- Impact: Metadata and programmatic version checks may be inconsistent with published version. Release tooling may fail or users get wrong version info.
- Fix approach: Sync both files to the same version. Use single source of truth (consider `pyproject.toml`) and read version dynamically in `__init__.py`.

**Overly Broad Exception Handling:**
- Issue: LLM initialization catches `Exception` without specificity; logs warning but doesn't re-raise
- Files: `folio/graph.py:251`
- Impact: Real errors (API keys missing, network issues) are silently suppressed with warnings. Users don't know LLM search is broken until they call it.
- Fix approach: Catch specific exceptions (`APIConnectionError`, `AuthenticationError`, etc.). Optionally re-raise with context, or make LLM optional in constructor with explicit flag.

## Known Bugs

**Deduplication During Alternative Label Collection:**
- Bug: Alternative labels are added without checking if `lang`-tagged and base versions conflict during XML parsing
- Symptoms: When `xml:lang` altLabels and plain altLabels coexist for the same value, deduplication may fail to catch duplicates
- Files: `folio/graph.py:657-667`
- Trigger: Ontology with altLabels like `<altLabel>Name</altLabel>` and `<altLabel xml:lang="en">Name</altLabel>` on same class
- Workaround: None; currently requires manual cleanup after parsing

**IRI Normalization Not Idempotent for Legacy Formats:**
- Bug: Multiple legacy URL formats map to same IRI, but normalization can fail for mixed formats
- Symptoms: IRI lookups fail for some legacy URL variations
- Files: `folio/graph.py:1105-1132`
- Trigger: Using legacy `soli:`, `lmss:` prefixes with mixed casing or non-standard formatting
- Workaround: Use normalized FOLIO IRIs when possible

## Security Considerations

**Unvalidated External Network Requests:**
- Risk: Network requests to GitHub and HTTP endpoints lack timeout enforcement and retry limits
- Files: `folio/graph.py:279-288`, `folio/graph.py:418-432`, `folio/graph.py:445-456`
- Current mitigation: `httpx` client used with `raise_for_status()` for HTTP errors
- Recommendations: 
  - Add explicit timeout parameter to all `httpx.Client()` calls (e.g., `timeout=30`)
  - Implement exponential backoff retry logic for transient failures
  - Add rate-limit detection and backoff
  - Validate URLs before use to prevent SSRF attacks

**Optional Dependency Conditional Logic:**
- Risk: Search functionality silently degrades if `rapidfuzz`, `marisa_trie`, or `alea_llm_client` are missing; no runtime error until used
- Files: `folio/graph.py:131-156`
- Current mitigation: Warnings logged if dependencies not found; methods check if modules are None
- Recommendations:
  - Raise `ImportError` in methods that require dependencies if they're not available (fail fast)
  - Consider making search a separate optional module rather than conditional imports in core module
  - Document required versions and compatibility in README

**No Input Validation on IRIs:**
- Risk: User-supplied IRIs passed to search, retrieval, and filtering functions are not validated for format or length
- Files: `folio/graph.py:1146-1167`, `folio/graph.py:1169-1189`
- Current mitigation: Normalization and dictionary lookup (fails gracefully with None return)
- Recommendations:
  - Add URI format validation using `urllib.parse`
  - Set max length limits on IRI strings
  - Add fuzzy matching to suggest similar IRIs on lookup failure

## Performance Bottlenecks

**Linear Search in Triples Filtering:**
- Problem: Triple filtering operations iterate entire triple list on every call
- Files: `folio/graph.py:1999-2018`, `folio/graph.py:2020-2056`
- Cause: Triples stored as list, no indexes on predicate/subject/object fields
- Improvement path: Build three separate indices (one per field) during parsing. Update `_filter_triples()` to use indexed lookup. Trade memory for O(1) lookup instead of O(n) scan.

**Cache Invalidation on Refresh:**
- Problem: Calling `refresh()` clears `_cached_triples` but doesn't clear `functools.cache` decorators on methods
- Files: `folio/graph.py:1260-1266`
- Cause: `@cache` decorator (lines 525, 1094, 1336, 1990) persists across refresh; old data may be returned
- Improvement path: Implement cache-clearing method that invalidates all cached methods when data changes. Use decorator wrapper that checks dirty flag.

**JSON-LD Serialization Allocates New Arrays Repeatedly:**
- Problem: `to_jsonld()` creates new list objects for every field, even empty ones
- Files: `folio/models.py:406-527`
- Cause: Pattern of `jsonld_data["field"] = []` on every conditional check
- Improvement path: Only allocate arrays when content exists. Pre-check item count before initializing.

**Large Trie Object Held in Memory:**
- Problem: If `marisa_trie` is initialized, trie object persists for entire program lifecycle
- Files: `folio/graph.py:160-230` (not shown, but initialization pattern)
- Cause: Trie built during `__init__` with full index
- Improvement path: Lazy-load trie on first search. Consider memory-mapped disk-based trie for very large ontologies.

## Fragile Areas

**OWL Parsing with Complex Restrictions:**
- Files: `folio/graph.py:580-618`
- Why fragile: Complex OWL restrictions (someValuesFrom, allValuesFrom, oneOf) require nested element traversal. Changes to XML structure or namespace handling break silently.
- Safe modification: Add unit tests for each restriction type. Use XPath selectors instead of manual traversal. Validate namespace mappings before parsing.
- Test coverage: No specific restriction-type test cases found in test file

**Alternative Label Handling (Multilingual Support):**
- Files: `folio/graph.py:657-667`, `folio/models.py:462-470`
- Why fragile: Logic to separate translations from altLabels relies on `xml:lang` attribute presence. Hidden labels are also added to altLabels. Order of operations matters.
- Safe modification: Separate translations fully into own collection. Dedup hidden labels against altLabels before adding. Document the behavior.
- Test coverage: Basic multilingual tests exist but no edge case coverage (duplicate translations, missing lang attribute)

**IRI Normalization with Legacy Prefixes:**
- Files: `folio/graph.py:1100-1132`
- Why fragile: Multiple legacy URL schemes (soli, lmss) hardcoded. Adding new scheme requires code change. Order of checks matters.
- Safe modification: Use regex pattern matching instead of sequential `startswith` checks. Consider building prefix map from config.
- Test coverage: Test exists for one branch; need comprehensive test for all legacy formats and edge cases

## Scaling Limits

**Triple Storage Unbounded in Memory:**
- Current capacity: Handles FOLIO 2.0.0 (several thousand classes) with <100MB footprint for triples
- Limit: With very large ontologies (100k+ classes), triple list becomes unbounded linear growth
- Scaling path: Implement triple store interface that can switch between in-memory list and disk-backed SQLite. Lazy-load triples on demand.

**LLM Context Window Usage:**
- Current capacity: Minimal system prompt + schema fits in token limit
- Limit: Once caching and expanded context are added (TODO at line 8), token usage may exceed limits for large searches
- Scaling path: Implement token counting before LLM calls. Use sliding window context if needed. Cache system prompt tokens once alea-llm-client supports it.

**Search Index Build Time:**
- Current capacity: Marisa trie builds in <5 seconds for FOLIO 2.0.0
- Limit: Very large ontologies (1M+ terms) will exceed reasonable build time during initialization
- Scaling path: Lazy-build search index on first use. Consider pre-built index files. Implement incremental index updates.

## Dependencies at Risk

**alea-llm-client Version Constraint:**
- Risk: Pinned to `>=0.1.1` with no upper bound until dev dependency. Upstream breaking changes will break search
- Files: `pyproject.toml:44`, `pyproject.toml:72`
- Impact: Search API changes in alea-llm-client will require code updates. Cannot use versions with token caching (planned feature).
- Migration plan: Add upper bound constraint once major version is released. Keep fork or wrapper of LLM calls to ease future migrations.

**lxml Library:**
- Risk: `lxml>=5.2.2` depends on C bindings; installation can fail on systems without build tools
- Files: `pyproject.toml:36`
- Impact: Installation failures on CI systems or containerized environments without C compiler
- Migration plan: Document build requirements. Consider pure-Python XML parser alternative (xml.etree, but slower). Add CI test on minimal image.

**marisa-trie (Optional Dependency):**
- Risk: Specialized library with limited maintenance; may not update for new Python versions
- Files: `pyproject.toml:43`, `pyproject.toml:70`
- Impact: Search degrades to linear search if marisa-trie not installable. No warnings until user calls search.
- Migration plan: Implement fallback pure-Python prefix tree. Consider replacing with standard library collections.defaultdict structure.

## Missing Critical Features

**No Ontology Validation:**
- Problem: Loaded OWL is not validated against FOLIO schema. Invalid or malformed data passes through silently.
- Blocks: Cannot guarantee data quality in downstream applications. Silent data loss possible (e.g., unimplemented element types).
- Recommendation: Add schema validator that checks for required fields, valid IRIs, and consistency constraints.

**No Concurrency Support in Mutable State:**
- Problem: FOLIO class is not thread-safe. Multiple threads accessing ontology simultaneously will cause data races.
- Blocks: Cannot use FOLIO in concurrent server applications without locks.
- Recommendation: Make FOLIO immutable after initialization, or add thread-safe wrapper class.

**No Change Notifications:**
- Problem: When `refresh()` is called, downstream code doesn't know ontology changed.
- Blocks: Caches at application level won't invalidate. Search results become stale.
- Recommendation: Implement observer pattern or callback mechanism for refresh events.

## Test Coverage Gaps

**LLM Search Methods Not Tested:**
- What's not tested: `search_by_llm()`, `parallel_search_by_llm()` methods with actual LLM responses
- Files: `folio/graph.py:1520-1660`
- Risk: LLM integration regressions won't be caught. Response parsing edge cases unknown.
- Priority: **High** - LLM is core feature advertised in documentation

**Complex OWL Constructs:**
- What's not tested: DatatypeProperty, AnnotationProperty, NamedIndividual, restriction types
- Files: `folio/graph.py:946-957`
- Risk: If FOLIO schema adds these elements, silent data loss won't be detected.
- Priority: **Medium** - Low current impact but future-proofing critical

**Error Cases in Network Loading:**
- What's not tested: Timeout handling, partial downloads, corrupted response bodies, rate limiting
- Files: `folio/graph.py:277-457`
- Risk: Applications fail ungracefully under poor network conditions.
- Priority: **Medium** - Important for reliability

**Multilingual Translations Edge Cases:**
- What's not tested: Duplicate translations, missing lang attribute, translation with same value as altLabel
- Files: `folio/graph.py:657-667`, `folio/models.py:462-470`
- Risk: Data loss in to_jsonld() when translations present.
- Priority: **High** - Known data loss bug

**Alternative Label Deduplication:**
- What's not tested: Deduplication when lang-tagged and base versions of same label coexist
- Files: `folio/graph.py:657-667`
- Risk: Duplicate labels in search results; inflated result counts.
- Priority: **Medium** - Recent fix but edge cases unknown

---

*Concerns audit: 2026-04-07*
