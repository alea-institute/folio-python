# Codebase Structure

**Analysis Date:** 2026-04-07

## Directory Layout

```
folio-python/
├── folio/                      # Main library package
│   ├── __init__.py             # Public API exports
│   ├── models.py               # Data models (OWLClass, OWLObjectProperty)
│   ├── graph.py                # Core FOLIO ontology service
│   ├── config.py               # Configuration management
│   └── logger.py               # Logging utilities
├── tests/                      # Test suite
│   └── test_folio.py           # Main test file
├── examples/                   # Usage examples
│   ├── initialize_client.py    # Initialization examples
│   ├── basic_search.py         # Search functionality
│   ├── basic_graph.py          # Graph traversal
│   ├── basic_taxonomy.py       # Taxonomy exploration
│   ├── basic_traversal.py      # Parent/child traversal
│   ├── basic_triples.py        # Triple queries
│   ├── basic_object_properties.py  # Object property queries
│   ├── semantic_connections.py # Semantic relationship finding
│   ├── property_categories.py  # Property usage analysis
│   ├── property_frequency.py   # Property frequency analysis
│   └── llm_search.py           # LLM-based semantic search
├── docs/                       # Sphinx documentation
│   ├── conf.py                 # Sphinx configuration
│   ├── index.md                # Documentation index
│   ├── examples.md             # Example documentation
│   └── folio/                  # Auto-generated module docs
├── docker/                     # Docker build files
├── .github/                    # GitHub workflows (CI/CD)
├── .planning/                  # GSD planning documents
├── pyproject.toml              # Project metadata and dependencies
├── README.md                   # Main documentation
├── CHANGES.md                  # Changelog
├── CONTRIBUTING.md             # Contributing guidelines
└── LICENSE                     # MIT license
```

## Directory Purposes

**folio/:**
- Purpose: Main library package with all source code
- Contains: Core modules for ontology loading, parsing, querying, and data models
- Key files: `graph.py` (largest, ~2164 lines), `models.py` (~552 lines)

**tests/:**
- Purpose: Test suite for library functionality
- Contains: Single `test_folio.py` file with pytest test cases
- Tests coverage: Initialization, loading, parsing, searching, graph traversal

**examples/:**
- Purpose: Executable usage examples demonstrating library features
- Contains: 11 Python scripts showing initialization, search, traversal, properties, and LLM integration
- Not included in distribution (per `pyproject.toml` excludes)

**docs/:**
- Purpose: Sphinx documentation source
- Contains: Configuration, index, examples guide, and auto-generated API docs
- Build target: Generates HTML documentation (hosted on ReadTheDocs)

**docker/:**
- Purpose: Docker containerization for documentation/development
- Contains: Dockerfile and related build files

**.github/:**
- Purpose: GitHub Actions CI/CD workflows
- Contains: Automated testing, linting, and publishing pipelines

**.planning/:**
- Purpose: GSD methodology planning documents
- Contains: Architecture, structure, testing, conventions, concerns analysis

## Key File Locations

**Entry Points:**
- `folio/__init__.py`: Package initialization, public API exports (lines 1-28)
- `folio/graph.py:167-254`: `FOLIO.__init__()` constructor, the main entry point for users

**Configuration:**
- `folio/config.py`: `FOLIOConfiguration` model, default constants, cache path definitions
- `pyproject.toml`: Project metadata, dependencies, tool configurations
- `config.json`: Example configuration file for users (minimal, shows structure)

**Core Logic:**
- `folio/graph.py:544-775`: `parse_owl_class()` - OWL class parsing logic
- `folio/graph.py:775-904`: `parse_owl_object_property()` - Property parsing logic
- `folio/graph.py:961-1012`: `parse_owl()` - Main parsing orchestrator, index building
- `folio/graph.py:1014-1043`: `get_subgraph()` - Recursive graph traversal
- `folio/graph.py:1146-1167`: `__getitem__()` - Direct IRI/index access
- `folio/graph.py:1289-1336`: `search_by_prefix()` - Trie-based prefix search
- `folio/graph.py:1370-1417`: `search_by_label()` - Fuzzy label search
- `folio/graph.py:2058-2137`: `find_connections()` - Semantic relationship queries

**Testing:**
- `tests/test_folio.py`: All test cases (~400+ lines)
- Pytest configuration in `pyproject.toml:131-132`

**Data Models:**
- `folio/models.py:15-26`: NSMAP namespace definitions
- `folio/models.py:29-80`: `OWLObjectProperty` class
- `folio/models.py:82-551`: `OWLClass` class with serialization methods

**Utilities:**
- `folio/logger.py`: `get_logger()` function for module-level logging
- `folio/graph.py:255-435`: Static methods for loading ontology from GitHub/HTTP

## Naming Conventions

**Files:**
- Source files: `lowercase_with_underscores.py` (e.g., `graph.py`, `config.py`)
- Example files: `lowercase_with_underscores.py` (e.g., `basic_search.py`, `llm_search.py`)
- Test files: `test_*.py` following pytest convention

**Classes:**
- Domain models: PascalCase (e.g., `OWLClass`, `OWLObjectProperty`)
- Configuration: PascalCase (e.g., `FOLIOConfiguration`)
- Enums: PascalCase (e.g., `FOLIOTypes`)

**Functions:**
- Methods and functions: snake_case (e.g., `parse_owl_class`, `search_by_label`, `get_subgraph`)
- Dunder methods: `__method_name__()` (e.g., `__init__`, `__getitem__`, `__contains__`)
- Static methods: snake_case with `@staticmethod` decorator

**Variables:**
- Module-level constants: UPPERCASE_WITH_UNDERSCORES (e.g., `DEFAULT_CACHE_DIR`, `OWL_THING`, `MIN_PREFIX_LENGTH`)
- Instance variables: snake_case (e.g., `self.classes`, `self.iri_to_index`, `self.label_trie`)
- Function parameters: snake_case (e.g., `source_type`, `max_depth`, `github_repo_owner`)

**Directories:**
- Package directories: lowercase (e.g., `folio/`)
- Documentation: `docs/`
- Tests: `tests/`
- Examples: `examples/`
- Docker: `docker/`

## Where to Add New Code

**New Feature / Search Method:**
- Primary code: `folio/graph.py` in the `FOLIO` class
- Pattern: Add method with signature following existing methods (e.g., `search_by_*`, `get_*`)
- Use `self.classes` list and existing indices for queries
- Populate indices if adding new search capability
- Tests: Add test case in `tests/test_folio.py`

**New Data Model / Serialization Format:**
- Implementation: Add method to `OWLClass` or `OWLObjectProperty` in `folio/models.py`
- Pattern: Follow `to_owl_xml()`, `to_markdown()`, `to_jsonld()` pattern
- Use `NSMAP` for namespace handling
- Tests: Add test in `tests/test_folio.py`

**New Query Type / Graph Operation:**
- Implementation: `folio/graph.py` in the `FOLIO` class
- Pattern: Leverage existing `get_subgraph()`, `get_children()`, `get_parents()` for traversal
- Index queries: Use `iri_to_index`, `label_to_index`, `alt_label_to_index` for lookups
- Tests: Add test case in `tests/test_folio.py`

**Configuration/Loading Logic:**
- Implementation: Extend `folio/config.py` for new config options, or `folio/graph.py` for new load/cache logic
- Pattern: Follow existing patterns in `FOLIOConfiguration`, `load_owl()`, `load_cache()`
- Maintain backward compatibility with existing cache structure

**Utilities/Helpers:**
- Simple logging: Use `folio/logger.py` via `get_logger(__name__)`
- New utility module: Create new file in `folio/` with snake_case name
- Export in `folio/__init__.py` if part of public API

**Examples / Documentation:**
- New examples: Add Python file to `examples/` following naming pattern
- Auto-generated docs: No action needed; Sphinx auto-discovers `folio/` modules
- Manual documentation: Update `docs/*.md` files

## Special Directories

**~/.folio/cache/:**
- Purpose: Local cache storage for downloaded ontology files
- Generated: Yes, created automatically on first FOLIO initialization
- Committed: No, excluded from git (user-local)
- Structure: `cache/{source_type}/{blake2b_hash}.owl`
- Cleanup: Manual deletion of cache/ subdirectory to clear

**htmlcov/:**
- Purpose: Test coverage report HTML output
- Generated: Yes, by pytest-cov after test runs
- Committed: No, excluded from git
- Usage: Open `htmlcov/index.html` in browser to view coverage

**dist/ and build/:**
- Purpose: Package distribution artifacts
- Generated: Yes, by hatchling during `pip install -e .` or `hatch build`
- Committed: No, excluded from git
- Cleanup: Safe to delete; will be regenerated as needed

**docs/_build/:**
- Purpose: Generated Sphinx documentation
- Generated: Yes, by `sphinx-build` or ReadTheDocs
- Committed: No, excluded from git
- Rebuild: `cd docs && make html`

**.pytest_cache/:**
- Purpose: Pytest metadata and cache
- Generated: Yes, by pytest
- Committed: No, excluded from git
- Cleanup: Safe to delete; regenerated on next test run

---

*Structure analysis: 2026-04-07*
