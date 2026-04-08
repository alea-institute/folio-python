# CLAUDE.md

## Project

folio-python is the Python library for FOLIO (Federated Open Legal Information Ontology). It loads, parses, searches, and traverses the FOLIO OWL ontology (~18k classes, ~100 object properties).

## Setup

```bash
uv sync          # installs dev + search extras
```

## Commands

### Tests

```bash
uv run pytest tests/            # full suite (includes benchmarks)
uv run pytest tests/ -k "not benchmark"  # skip benchmarks (faster)
```

### Linting and formatting

```bash
ruff check --fix folio/ tests/  # lint + autofix
ruff format folio/ tests/       # format
ty check folio/                 # type check (47 pre-existing diagnostics from optional imports and lxml types)
```

Run all three before committing. `ruff check` and `ruff format` should be clean. `ty check` has known pre-existing issues with optional `marisa_trie`/`rapidfuzz` imports and `lxml.etree` types — don't introduce new diagnostics.

## Architecture

- `folio/graph.py` — Main `FOLIO` class: loading, parsing, indexing, search, traversal, query
- `folio/models.py` — `OWLClass` and `OWLObjectProperty` pydantic models
- `folio/config.py` — Default configuration (GitHub repo, cache dir, etc.)
- `folio/logger.py` — Logging setup

## Key patterns

- `FOLIO[iri]` returns `OWLClass | None` — the primary lookup method
- `folio.get_property(iri)` returns `OWLObjectProperty | None`
- Search methods (`search_by_label`, `search_by_definition`, `search_by_prefix`) require `[search]` extra (rapidfuzz, marisa-trie)
- `query()` and `query_properties()` do structured filtering with composable text + structural filters
- Branch getters (`get_areas_of_law()`, etc.) all delegate to `get_children(root_iri, max_depth)`
- Optional imports (`rapidfuzz`, `marisa_trie`, `alea_llm_client`) are guarded with try/except

## Dependencies

- **Core:** pydantic, lxml, httpx
- **[search] extra:** rapidfuzz, marisa-trie, alea-llm-client
- `alea_llm_client` is only needed for LLM-powered search (`search_by_llm`)
