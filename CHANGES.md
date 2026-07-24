Version 0.3.7 (2026-07-24)
---------------------------
* Security: Bumped `lxml` floor to `>=6.1.0` (locked 6.1.1) — CVE-2026-41066 / GHSA-vfmq-68hx-4jfw, XXE to local files via the default configuration of `iterparse()` and `ETCompatXMLParser()`
* Security: Lockfile bumps for transitive dependencies — `idna` 3.11 -> 3.18 (CVE-2026-45409), `urllib3` 2.6.3 -> 2.7.0 (CVE-2026-44431, CVE-2026-44432), `soupsieve` 2.8.3 -> 2.9.1 (CVE-2026-49476, CVE-2026-49477)
* Security: Dev toolchain bumps for CVE-2025-71176 (pytest tmpdir handling) — `pytest` `>=9.0.3,<10`, plus compatible `pytest-asyncio` `>=1.0.0,<2`, `pytest-benchmark` `>=5.1.0,<6`, `pytest-cov` `>=7.0.0,<8`
* No public API changes; full test suite (64 tests) passes unchanged

Version 0.3.6 (2026-04-08)
---------------------------
* Docs: Migrated user-facing documentation to https://openlegalstandard.org/resources/folio-python-library — comprehensive 9-page reference covering install, search, query, taxonomy, properties, serialization, LLM integration, and a complete API surface (alea-institute/folio-python#14)
* Removed: `docs/` directory (Sphinx site that targeted the broken folio-python.readthedocs.io)
* Removed: `.readthedocs.yaml` (RTD config no longer needed)
* Removed: `.github/workflows/publish.yml` (Trusted Publisher workflow that was never configured on PyPI; releases are published locally via `uv build && uvx twine upload`)
* Updated: README documentation link now points at openlegalstandard.org; logo path moved from `docs/_static/folio-logo.png` to `assets/folio-logo.png`
* Updated: CONTRIBUTING.md notes that user-facing docs live in the openlegalstandard.org repo and should be updated alongside any public-API changes

Version 0.3.5 (2026-04-08)
---------------------------
* Added: `case_sensitive` parameter (default `False`) on `search_by_prefix()` — lowercase and mixed-case queries now match labels via a parallel lowercase MARISA trie using `str.casefold()` for Unicode-safe folding
* Changed: `search_by_prefix()` now ranks primary-label matches before alt-label matches and deduplicates results by IRI; affects default ordering for queries like `Mich`, `Tax`, and `Cal`
* Fixed: Case-sensitive `search_by_prefix()` no longer returns duplicate entries when a class matches a prefix via both its label and an alt-label
* Fixed: Prefix caches are now cleared on `refresh()` to avoid stale results
* Fixed: `folio.__version__` was stuck at `0.3.0` since v0.3.0; now tracks `pyproject.toml`

Version 0.3.4 (2026-03-16)
---------------------------
* Fixed: Include lang-tagged altLabels in search index with deduplication — 90% of altLabels were previously invisible to `search_by_label()`

Version 0.3.3 (2026-03-15)
---------------------------
* Fixed: Drop max_tokens from search_by_llm, bump alea-llm-client>=0.3.3

Version 0.3.2 (2026-03-15)
---------------------------
* Fixed: Bump alea-llm-client>=0.3.2 for model-aware get_llm_kwargs

Version 0.3.1 (2026-03-15)
---------------------------
* Added effort/tier params to FOLIO constructor for LLM search configuration
* Updated LLM defaults

Version 0.3.0 (2026-03-15)
---------------------------
* Added `FOLIO.query()` method for structured concept queries with composable text and structural filters
* Added `FOLIO.query_properties()` method for structured property queries with domain/range/inverse filters
* Both methods support four match modes: substring (default), exact, regex, and fuzzy
* Query filters include: label, definition, alt_label, example, any_text, branch, parent_iri, has_children, deprecated, country
* Property query filters include: label, definition, domain_iri, range_iri, has_inverse

Version 0.2.1 (2026-03-15)
---------------------------
* Fixed: Index preferred_label (skos:prefLabel) for search — prefLabels are now included in search indices
* Added PyPI publish workflow for automated releases via GitHub

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
