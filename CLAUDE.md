<!-- GSD:project-start source:PROJECT.md -->
## Project

**Case-Insensitive Prefix Search for folio-python**

Adding case-insensitive prefix search to the folio-python library's `search_by_prefix()` method. Currently, prefix search is case-sensitive because the underlying `marisa-trie` stores labels in their original case (e.g., "Securities Fraud", "DUI", "M&A Practice Components"), but all realistic callers lowercase their input before searching — causing 100% silent miss rates.

**Core Value:** Prefix search must return correct results regardless of input casing — `search_by_prefix("securit")` must match "Securities Fraud" just as `search_by_prefix("Securit")` does today.

### Constraints

- **Backward compatibility**: Existing `search_by_prefix("Securit")` must continue to work — the new `case_sensitive=False` default returns a superset of what `case_sensitive=True` would return
- **No new dependencies**: Only uses existing `marisa_trie` (already a dependency)
- **Branch strategy**: Feature branch `feature/case-insensitive-prefix` targeting `main`
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.10+ - Full library implementation; supports 3.10, 3.11, 3.12, 3.13
- XML/OWL - Ontology format (FOLIO.owl files parsed via lxml)
- TOML - Project configuration (`pyproject.toml`)
- YAML - CI/CD and documentation config
- JSON - Runtime configuration files
## Runtime
- Python 3.10–3.13 (configurable, currently testing on 3.13)
- UV (fast Python package manager) - Primary
- pip - Fallback in CI/CD workflows
- poetry - Used in legacy CI workflow (`.github/workflows/CI.yml` line 56)
- Lockfile: `uv.lock` present (reproducible builds)
## Frameworks
- pydantic 2.8.2+ - Data validation and OWL model definitions (`folio/models.py`)
- lxml 5.2.2+ - XML/OWL ontology parsing (`folio/graph.py`)
- httpx 0.27.2+ - HTTP client for GitHub API and remote ontology loading (`folio/graph.py` lines 31, 279–281, 420, 447)
- rapidfuzz 3.10.0–3.x - Fuzzy string matching for label search (`folio/graph.py` lines 132–134, 1357–1363)
- marisa-trie 1.2.0–1.x - Trie-based efficient label indexing (`folio/graph.py` lines 138–139, 1005, 1012)
- alea-llm-client 0.1.1+ - AI model integration for semantic search (`folio/graph.py` lines 144–152, 247)
- pytest 8.3.1–8.x - Test runner
- pytest-asyncio 0.23.8–0.24.x - Async test support
- pytest-benchmark 4.0.0–4.x - Performance benchmarking
- pytest-cov 5.0.0–5.x - Code coverage reporting
- black 24.4.2–24.x - Code formatting
- pylint 3.2.7–3.x - Linting
- ruff (v0.6.3) - Fast linting and formatting via pre-commit
- isort - Import sorting (configured via `pyproject.toml` lines 127–129)
- types-lxml 2024.8.7–2024.x - Type hints for lxml
- Sphinx 7.4.7–7.x - Documentation generation
- myst-parser 3.0.1–3.x - Markdown support in Sphinx
- sphinx-book-theme 1.1.3–1.x - Modern Sphinx theme
- sphinxcontrib-mermaid 0.9.2–0.10.x - Diagram support
- sphinx-copybutton 0.5.2–0.6.x - Copy-to-clipboard for code
- sphinxext-opengraph 0.9.1–0.10.x - Open Graph meta tags
- sphinx-plausible 0.1.2–0.2.x - Privacy-focused analytics
- hatchling (build backend in `pyproject.toml` line 106)
- pip - Build tool wrapper
## Key Dependencies
- pydantic - Validates and structures OWL class/property models; required for all parsing
- lxml - Parses OWL XML ontology files; no fallback
- httpx - Fetches ontology from GitHub API (`https://api.github.com`) and GitHub Objects (`https://raw.githubusercontent.com`)
- alea-llm-client 0.1.3 (in uv.lock) - Wraps OpenAI API for LLM-based semantic search; graceful fallback if not installed (`folio/graph.py` lines 144–152)
- rapidfuzz - Enables fuzzy label search; degrades gracefully (`folio/graph.py` line 135)
- marisa-trie - Enables prefix-based label trie search; degrades gracefully (`folio/graph.py` line 141)
## Configuration
- Configuration loaded from `~/.folio/config.json` via `FOLIOConfiguration.load_config()` in `folio/config.py` lines 87–128
- Environment variables: None required; all config via JSON file or constructor parameters
- GitHub API: Accessed via httpx with default base URL `https://api.github.com` (`folio/config.py` line 23)
- GitHub Objects: Accessed via `https://raw.githubusercontent.com` for raw file downloads (`folio/config.py` line 24)
- `pyproject.toml` lines 75–79: UV default dependency groups include `["dev", "search"]`
- ruff configuration: black profile, 120 character line length (`.pre-commit-config.yaml` line 21)
- isort configuration: black profile, 120 character line length (`pyproject.toml` lines 127–129)
- Source type: `"github"` (default) or `"http"` (`folio/config.py` lines 46–47)
- GitHub repo owner: `"alea-institute"` (default, `folio/config.py` line 33)
- GitHub repo name: `"FOLIO"` (default, `folio/config.py` line 34)
- GitHub repo branch: `"2.0.0"` (default, `folio/config.py` line 35)
- HTTP URL: Optional, only for `"http"` source type (`folio/config.py` line 30)
- Caching: Enabled by default at `~/.folio/cache/` (`folio/graph.py` line 110)
## Platform Requirements
- Python 3.10+ with pip/UV
- lxml build dependencies (libxml2, libxslt on Ubuntu: `sudo apt-get install libxml2-dev libxslt1-dev`)
- Git (for cloning FOLIO ontology from GitHub)
- Pre-commit hooks configured (ruff, gitleaks security scanner)
- Python 3.10+
- Network access to `https://api.github.com` and `https://raw.githubusercontent.com` (if using GitHub source)
- Local filesystem access for caching (`~/.folio/cache/`)
- OpenAI API key environment variable if using LLM search (`OPENAI_API_KEY` for alea-llm-client)
- GitHub Actions workflow triggers on release (publish.yml) and push/PR to main/dev (CI.yml)
- PyPI publishing via `pypa/gh-action-pypi-publish@release/v1` (trusted publishing, OIDC)
- Read the Docs integration: Build configuration in `.readthedocs.yaml` lines 1–32 (Python 3.11, Sphinx)
- Supported architectures: x86_64, x86, aarch64, armv7, s390x, ppc64le (via maturin in CI.yml)
## Dependency Groups
- rapidfuzz 3.10.0–3.x
- marisa-trie 1.2.0–1.x
- alea-llm-client 0.1.1+
- Testing: pytest, pytest-asyncio, pytest-benchmark, pytest-cov
- Linting: pylint, black (deprecated in favor of ruff)
- Documentation: Sphinx, myst-parser, sphinx-book-theme, sphinxcontrib-mermaid
- Type hints: types-lxml
- Same as `[project.optional-dependencies.search]` but with explicit versions (rapidfuzz 3.9.7+, alea-llm-client <0.2)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Module files use lowercase with underscores: `graph.py`, `models.py`, `logger.py`, `config.py`
- Example files use lowercase with underscores describing functionality: `basic_taxonomy.py`, `initialize_client.py`, `property_categories.py`
- Use PascalCase: `FOLIO`, `OWLClass`, `OWLObjectProperty`, `FOLIOConfiguration`, `FOLIOTypes`
- Enum members use UPPER_CASE_WITH_UNDERSCORES: `ACTOR_PLAYER`, `AREA_OF_LAW`, `ASSET_TYPE`
- Use snake_case: `get_logger()`, `load_owl_github()`, `search_by_label()`, `to_markdown()`, `is_valid()`
- Conversion methods use `to_*()` pattern: `to_owl_element()`, `to_owl_xml()`, `to_json()`, `to_jsonld()`, `to_markdown()`
- Factory methods use `from_*()` pattern: `from_json()`
- Getter methods use `get_*()` pattern: `get_logger()`, `get_types()`, `get_property()`, `get_triples_by_predicate()`
- Filter/search methods use `search_*()` pattern: `search_by_prefix()`, `search_by_label()`, `search_by_definition()`
- Use snake_case for attributes and local variables: `source_type`, `http_url`, `github_repo_owner`, `cache_path`, `iri_to_index`
- Dictionary keys use lowercase with underscores: `"folio"`, `"repo_owner"`, `"use_cache"`
- Private/internal attributes do not use underscore prefix in Pydantic models (Field definitions)
- Always use type hints for function parameters and return types: `def get_logger(name: str) -> logging.Logger:`
- Use Python 3.10+ union syntax with `|` where appropriate: `str | Path`, `Optional[str]`, `Dict[str, int]`
- Use forward references for self-referencing types: `from __future__ import annotations`
- Generic types use fully qualified names: `Dict`, `List`, `Optional`, `Tuple`, `Literal`
## Code Style
- Line length: 120 characters max (configured in `pyproject.toml`)
- Formatter: `black` and `ruff` (via pre-commit hooks)
- Indentation: 4 spaces
- Primary linter: `pylint` configured in `pyproject.toml`
- Pre-commit hooks: `ruff` (check --fix), `ruff-format`, `pre-commit-hooks`
- pylint disabled rules: `line-too-long`, `too-few-public-methods`, `no-self-argument`, `cyclic-import`
- File-level pylint directives used: `# pylint: disable=fixme,no-member,unsupported-assignment-operation,too-many-lines,too-many-public-methods,invalid-name`
## Import Organization
- Not used; imports are explicit with relative module names
- Configuration imports from `folio.config`, logging from `folio.logger`, models from `folio.models`
## Docstrings
## Comments
- Explain "why" not "what" — code that is self-documenting via clear naming does not need comments
- Use comments for complex logic, non-obvious decisions, or important caveats
- Include comments for workarounds or temporary solutions
- Used to mark incomplete work: `TODO: think about future-proofing for next-gen roadmap.`
- Used to mark needed implementations: `TODO: implement token caching layer in system prompt for search`
- Flagged by pylint with `fixme` disabled to allow checking
## Module Constants
## Data Validation
## Error Handling
## Logging
- `LOGGER.warning()` for optional features that could not be enabled or recoverable issues
- `LOGGER.info()` for significant operations (loading ontology, parsing, initialization)
- Default level: WARNING (set in `folio/logger.py`)
## Function Design
- Use keyword arguments for better readability with multiple parameters
- Provide reasonable defaults for optional parameters: `use_cache: bool = True`
- Use static methods for utility functions not requiring instance state: `@staticmethod def list_branches(...)`
- Always include return type hint
- Return `None` explicitly when appropriate: `-> None`
- Return typed collections: `-> List[str]`, `-> Dict[str, int]`, `-> Optional[str]`
- Methods that return another class instance use the class name in quotes for forward references
## Module Design
- `folio/__init__.py` — Package exports and version metadata
- `folio/graph.py` — Main FOLIO class and FOLIOTypes enum
- `folio/models.py` — OWLClass, OWLObjectProperty, NSMAP definitions
- `folio/config.py` — Configuration management and defaults
- `folio/logger.py` — Logging utility
## Class Design
- Provides validation, serialization (`model_dump()`, `model_dump_json()`)
- Field descriptors document each attribute with SKOS/RDF semantics
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Monolithic `FOLIO` class serves as the main orchestrator for ontology access and querying
- Data layer separates domain models (`OWLClass`, `OWLObjectProperty`) from the graph structure
- Pluggable external data sources (GitHub or HTTP URL)
- Optional search features using specialized indices (trie-based prefix search, fuzzy matching)
- Client-agnostic LLM integration for semantic search
## Layers
- Purpose: Define domain structures for OWL ontology entities
- Location: `folio/models.py`
- Contains: `OWLClass`, `OWLObjectProperty` (Pydantic BaseModel classes), namespace map (`NSMAP`)
- Depends on: `pydantic`, `lxml` (for serialization)
- Used by: `folio/graph.py` during parsing and data access
- Purpose: Manage source and caching configuration
- Location: `folio/config.py`
- Contains: `FOLIOConfiguration` class, default constants for GitHub/HTTP sources, cache paths
- Depends on: `pydantic` for model validation
- Used by: `folio/graph.py` during initialization
- Purpose: Provide standardized logger instances
- Location: `folio/logger.py`
- Contains: `get_logger()` function that returns configured `logging.Logger` instances
- Depends on: Standard `logging` module
- Used by: All modules for debug/warning output
- Purpose: Load, parse, index, and query the FOLIO ontology
- Location: `folio/graph.py`
- Contains: `FOLIO` class (main orchestrator), `FOLIOTypes` enum, type mapping constants
- Depends on: `lxml.etree`, `httpx`, `pydantic`, optionally `rapidfuzz`, `marisa_trie`, `alea_llm_client`
- Used by: Public API exported from `folio/__init__.py`
## Data Flow
- Ontology state is immutable after `parse_owl()` completes
- All indices are read-only maps built once at initialization
- `refresh()` method reinitializes the entire FOLIO instance to reload ontology
- Triples are frozen in `_cached_triples` tuple after parsing
## Key Abstractions
- Purpose: Represent an OWL class from the FOLIO ontology
- Examples: `folio/models.py` lines 82-551
- Pattern: Pydantic BaseModel with semantic metadata fields (labels, definitions, examples, translations)
- Provides serialization: `to_owl_element()`, `to_owl_xml()`, `to_markdown()`, `to_jsonld()`, `to_json()`
- Purpose: Represent an OWL object property (relationships between classes)
- Examples: `folio/models.py` lines 29-80
- Pattern: Pydantic BaseModel with domain/range constraints
- Used by: Property queries and triple generation
- Purpose: Unified access point for ontology querying and traversal
- Examples: `folio/graph.py` lines 159-2164
- Pattern: Singleton-like class with static factory methods and instance state
- Key state: `classes` list, `object_properties` list, index mappings, cached triples
- Duality: Supports both direct IRI lookups (fast, O(1)) and semantic searches (slower, O(n) or LLM-based)
- Purpose: Provide a known set of FOLIO ontology categories
- Examples: `folio/graph.py` lines 48-104
- Pattern: Python Enum mapping human-readable category names to category IRIs
- Used by: Helper methods like `get_areas_of_law()`, `get_player_actors()`, etc.
## Entry Points
- Location: `folio/__init__.py`
- Exports: `FOLIO`, `FOLIOTypes`, `FOLIO_TYPE_IRIS`, `OWLClass`, `OWLObjectProperty`, `NSMAP`
- Usage: `from folio import FOLIO; folio = FOLIO()`
- Location: `folio/graph.py:167-254`
- Triggers: Module initialization, instantiation by users
- Responsibilities: Load ontology from source, parse OWL, initialize indices, optionally set up LLM
- `FOLIO.load_owl_github()` - Load directly from GitHub repository
- `FOLIO.load_owl_http()` - Load directly from HTTP URL
- `FOLIO.list_branches()` - List available branches in GitHub repo
- Used for: Alternative initialization paths, testing, version selection
## Error Handling
- Dependency checks via `importlib.util.find_spec()`: Optional dependencies like `rapidfuzz`, `marisa_trie`, `alea_llm_client` logged as warnings when unavailable
- HTTP errors wrapped as `RuntimeError` with context (e.g., "Error loading ontology from {url}")
- IRI normalization handles legacy URL schemes gracefully with fallback prefixes
- Missing or invalid classes return `None` instead of raising exceptions
- XML parsing uses `lxml.etree.XMLParser()` with UTF-8 encoding and strict namespace handling
## Cross-Cutting Concerns
- Approach: Per-module loggers via `get_logger(__name__)`
- Used for: Load/parse timing, cache hits/misses, dependency availability, IRI resolution warnings
- Level: WARNING by default; DEBUG available for detailed trace information
- Approach: Pydantic models enforce field types and defaults
- `OWLClass.is_valid()` checks if label is present (minimal validation)
- IRI normalization handles multiple legacy URL schemes
- Approach: None required; uses public GitHub API and public HTTP URLs
- GitHub API calls use basic Accept headers without auth tokens (subject to rate limits)
- Can be extended via custom LLM providers through `alea_llm_client`
- Approach: File-based cache under `~/.folio/cache/{source_type}/{blake2b_hash}.owl`
- Hash keys based on source parameters: GitHub repo/branch, HTTP URL
- Transparent to user via `use_cache` flag in constructor
- No TTL or invalidation beyond manual deletion
- Approach: Multiple indices for different query types
- `iri_to_index`: Direct IRI → class position
- `label_to_index`: Exact label matches → list of indices (handles synonyms)
- `alt_label_to_index`: Alternative label matches → list of indices
- `_label_trie`: Prefix matching via `marisa_trie` (only if library available)
- Triple index: Cached tuple of (subject, predicate, object) triples for semantic queries
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
