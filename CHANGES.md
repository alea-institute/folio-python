Version 0.3.0 (2026-07-07)
---------------------------
* Case-insensitive prefix search: `search_by_prefix()` now matches regardless of input casing via a parallel lowercase trie + bridge dict (e.g., `search_by_prefix("securit")` matches "Securities Fraud")
* New `case_sensitive: bool = False` parameter on `search_by_prefix()` — pass `case_sensitive=True` to preserve the pre-0.3.0 exact-case behavior
* No new dependencies — reuses the existing `marisa-trie`; a pure-Python fallback provides equivalent case-insensitive results when `marisa-trie` is unavailable
* Results are de-duplicated by class with primary-label matches ranked before alt-label matches, then by length
* Fixed pre-existing `refresh()` staleness — both the prefix cache and the new case-insensitive cache are now cleared when the ontology reloads

Version 0.2.0 (2024-04-17)
---------------------------
* Added support for OWL Object Properties, enabling semantic relationship exploration
* Added methods to search and filter by property types, domains, and ranges
* Added functionality to find connections between entities using labeled relationships
* Improved handling of rdfs:seeAlso relationships, including those defined via owl:Restriction
* Added new examples demonstrating property usage and semantic connections

Version 0.1.5 (2024-11-08)
---------------------------
* Adding support for LLM-backed (decoder) search, e.g., via OpenAI, Anthropic, VLLM, Together

Version 0.1.4 (2024-09-04)
---------------------------
* Add prefix search for typeahead/search bars (with optional trie-based search)
* Enhanced sort order for _basic_search (search_by_label, search_by_definition)


Version 0.1.3 (2024-09-03)
---------------------------
* Separate rapidfuzz dependency into optional [search] extra


Version 0.1.2 (2024-09-02)
---------------------------
* Added JSON-LD serialization support
* Adding shorthand namespace support (e.g., folio:R09...)
* Fixed dc:description type conversion (Element -> str)


Version 0.1.1 (2024-09-01)
---------------------------
* Fix nested f-string formatting issue with older Python versions

Version 0.1.0 (2024-09-01)
---------------------------
* First release of the FOLIO Python library.
