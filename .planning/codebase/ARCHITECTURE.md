# Architecture

**Analysis Date:** 2026-04-07

## Pattern Overview

**Overall:** Single-responsibility ontology service with a clear data loading, parsing, and query layer.

**Key Characteristics:**
- Monolithic `FOLIO` class serves as the main orchestrator for ontology access and querying
- Data layer separates domain models (`OWLClass`, `OWLObjectProperty`) from the graph structure
- Pluggable external data sources (GitHub or HTTP URL)
- Optional search features using specialized indices (trie-based prefix search, fuzzy matching)
- Client-agnostic LLM integration for semantic search

## Layers

**Data Models:**
- Purpose: Define domain structures for OWL ontology entities
- Location: `folio/models.py`
- Contains: `OWLClass`, `OWLObjectProperty` (Pydantic BaseModel classes), namespace map (`NSMAP`)
- Depends on: `pydantic`, `lxml` (for serialization)
- Used by: `folio/graph.py` during parsing and data access

**Configuration:**
- Purpose: Manage source and caching configuration
- Location: `folio/config.py`
- Contains: `FOLIOConfiguration` class, default constants for GitHub/HTTP sources, cache paths
- Depends on: `pydantic` for model validation
- Used by: `folio/graph.py` during initialization

**Logging:**
- Purpose: Provide standardized logger instances
- Location: `folio/logger.py`
- Contains: `get_logger()` function that returns configured `logging.Logger` instances
- Depends on: Standard `logging` module
- Used by: All modules for debug/warning output

**Core Graph Service:**
- Purpose: Load, parse, index, and query the FOLIO ontology
- Location: `folio/graph.py`
- Contains: `FOLIO` class (main orchestrator), `FOLIOTypes` enum, type mapping constants
- Depends on: `lxml.etree`, `httpx`, `pydantic`, optionally `rapidfuzz`, `marisa_trie`, `alea_llm_client`
- Used by: Public API exported from `folio/__init__.py`

## Data Flow

**Initialization Flow:**

1. **Create FOLIO instance** → `FOLIO.__init__()` captures source config (github/http, caching preference, LLM instance)
2. **Load OWL file** → `FOLIO.load_owl()` checks cache first, then fetches from GitHub or HTTP
3. **Parse XML** → `FOLIO.parse_owl()` streams XML parsing with `lxml`, dispatches to specialized parsers
4. **Parse Classes** → `FOLIO.parse_owl_class()` creates `OWLClass` instances, populates indices
5. **Parse Properties** → `FOLIO.parse_owl_object_property()` creates `OWLObjectProperty` instances
6. **Build Graph** → `parse_owl()` constructs class hierarchy edges after all nodes are parsed
7. **Build Indices** → Populate `iri_to_index`, `label_to_index`, `alt_label_to_index`, trie structure if `marisa_trie` available

**Query Flow:**

1. **Direct Access** → `folio[iri]` or `folio[index]` uses `__getitem__()` with `iri_to_index` for O(1) lookup
2. **Label Search** → `search_by_label()` uses fuzzy matching via `rapidfuzz`
3. **Prefix Search** → `search_by_prefix()` uses trie-based prefix matching via `marisa_trie`
4. **Definition Search** → `search_by_definition()` uses fuzzy matching on definition field
5. **Semantic Search** → `parallel_search_by_llm()` queries LLM with formatted class batches, reranks results
6. **Traversal** → `get_subgraph()`, `get_children()`, `get_parents()` traverse class hierarchy via `sub_class_of` and `parent_class_of` fields

**State Management:**
- Ontology state is immutable after `parse_owl()` completes
- All indices are read-only maps built once at initialization
- `refresh()` method reinitializes the entire FOLIO instance to reload ontology
- Triples are frozen in `_cached_triples` tuple after parsing

## Key Abstractions

**OWLClass:**
- Purpose: Represent an OWL class from the FOLIO ontology
- Examples: `folio/models.py` lines 82-551
- Pattern: Pydantic BaseModel with semantic metadata fields (labels, definitions, examples, translations)
- Provides serialization: `to_owl_element()`, `to_owl_xml()`, `to_markdown()`, `to_jsonld()`, `to_json()`

**OWLObjectProperty:**
- Purpose: Represent an OWL object property (relationships between classes)
- Examples: `folio/models.py` lines 29-80
- Pattern: Pydantic BaseModel with domain/range constraints
- Used by: Property queries and triple generation

**FOLIO Graph Service:**
- Purpose: Unified access point for ontology querying and traversal
- Examples: `folio/graph.py` lines 159-2164
- Pattern: Singleton-like class with static factory methods and instance state
- Key state: `classes` list, `object_properties` list, index mappings, cached triples
- Duality: Supports both direct IRI lookups (fast, O(1)) and semantic searches (slower, O(n) or LLM-based)

**Type Categories Enum:**
- Purpose: Provide a known set of FOLIO ontology categories
- Examples: `folio/graph.py` lines 48-104
- Pattern: Python Enum mapping human-readable category names to category IRIs
- Used by: Helper methods like `get_areas_of_law()`, `get_player_actors()`, etc.

## Entry Points

**Public Package API:**
- Location: `folio/__init__.py`
- Exports: `FOLIO`, `FOLIOTypes`, `FOLIO_TYPE_IRIS`, `OWLClass`, `OWLObjectProperty`, `NSMAP`
- Usage: `from folio import FOLIO; folio = FOLIO()`

**FOLIO Constructor:**
- Location: `folio/graph.py:167-254`
- Triggers: Module initialization, instantiation by users
- Responsibilities: Load ontology from source, parse OWL, initialize indices, optionally set up LLM

**Static Factory Methods:**
- `FOLIO.load_owl_github()` - Load directly from GitHub repository
- `FOLIO.load_owl_http()` - Load directly from HTTP URL
- `FOLIO.list_branches()` - List available branches in GitHub repo
- Used for: Alternative initialization paths, testing, version selection

## Error Handling

**Strategy:** Exceptions propagate up; logging captures warnings for missing dependencies or network issues

**Patterns:**
- Dependency checks via `importlib.util.find_spec()`: Optional dependencies like `rapidfuzz`, `marisa_trie`, `alea_llm_client` logged as warnings when unavailable
- HTTP errors wrapped as `RuntimeError` with context (e.g., "Error loading ontology from {url}")
- IRI normalization handles legacy URL schemes gracefully with fallback prefixes
- Missing or invalid classes return `None` instead of raising exceptions
- XML parsing uses `lxml.etree.XMLParser()` with UTF-8 encoding and strict namespace handling

## Cross-Cutting Concerns

**Logging:**
- Approach: Per-module loggers via `get_logger(__name__)`
- Used for: Load/parse timing, cache hits/misses, dependency availability, IRI resolution warnings
- Level: WARNING by default; DEBUG available for detailed trace information

**Validation:**
- Approach: Pydantic models enforce field types and defaults
- `OWLClass.is_valid()` checks if label is present (minimal validation)
- IRI normalization handles multiple legacy URL schemes

**Authentication:**
- Approach: None required; uses public GitHub API and public HTTP URLs
- GitHub API calls use basic Accept headers without auth tokens (subject to rate limits)
- Can be extended via custom LLM providers through `alea_llm_client`

**Caching:**
- Approach: File-based cache under `~/.folio/cache/{source_type}/{blake2b_hash}.owl`
- Hash keys based on source parameters: GitHub repo/branch, HTTP URL
- Transparent to user via `use_cache` flag in constructor
- No TTL or invalidation beyond manual deletion

**Search Indices:**
- Approach: Multiple indices for different query types
- `iri_to_index`: Direct IRI → class position
- `label_to_index`: Exact label matches → list of indices (handles synonyms)
- `alt_label_to_index`: Alternative label matches → list of indices
- `_label_trie`: Prefix matching via `marisa_trie` (only if library available)
- Triple index: Cached tuple of (subject, predicate, object) triples for semantic queries

---

*Architecture analysis: 2026-04-07*
