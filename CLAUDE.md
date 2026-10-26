# CLAUDE.md

## Project

folio-python is the Python library for FOLIO (Federated Open Legal Information Ontology). It loads, parses, searches, and traverses the FOLIO OWL ontology (~18k classes, ~100 object properties).

## Setup

```bash
uv sync --frozen # installs locked dev + search groups
```

## Commands

### Tests

```bash
uv run pytest tests/            # full suite (includes benchmarks)
uv run pytest tests/ -k "not benchmark"  # skip benchmarks (faster)
```

### Linting and formatting

```bash
uv run --frozen ruff check --fix folio/ tests/  # lint + autofix
uv run --frozen ruff format folio/ tests/       # format
uv run --frozen ty check folio/ # targets Python 3.10; zero diagnostics required
```

Run all three before committing; each must pass. The locked ty and types-lxml versions reproduce the zero-diagnostic baseline. See `CONTRIBUTING.md` for deterministic coverage, isolated core-only checks, and dependency audits; `docs/plans/evidence/fp-4-hygiene.md` records the measured results.

## Architecture

- `folio/graph.py` — Main `FOLIO` class: loading, parsing, indexing, search, traversal, query
- `folio/models.py` — `OWLClass` and `OWLObjectProperty` pydantic models
- `folio/config.py` — Default configuration (GitHub repo, cache dir, etc.)
- `folio/logger.py` — Logging setup

## Key patterns

- `FOLIO[iri]` returns `OWLClass | None` — the primary lookup method
- `folio.get_property(iri)` returns `OWLObjectProperty | None`
- Fuzzy search (`search_by_label`, `search_by_definition`) requires the `[search]` extra; `search_by_prefix` has a core-only Python fallback
- `query()` and `query_properties()` do structured filtering with composable text + structural filters
- Branch getters (`get_areas_of_law()`, etc.) all delegate to `get_children(root_iri, max_depth)`
- Optional imports (`rapidfuzz`, `marisa_trie`, `alea_llm_client`) are guarded with try/except

## Dependencies

- **Core:** pydantic, lxml, httpx
- **[search] extra:** rapidfuzz, marisa-trie, alea-llm-client
- `alea_llm_client` is only needed for LLM-powered search (`search_by_llm`)
