# Third-Party Licenses & Attribution

folio-python is licensed **MIT** (see `LICENSE`). It incorporates the open-source components below.

## Openly-licensed data

### FOLIO ontology — CC-BY 4.0

folio-python is a client library whose entire purpose is to **fetch, parse, and redistribute** the FOLIO ontology at runtime. By default it loads `FOLIO.owl` directly from the `alea-institute/FOLIO` GitHub repository (or a configured HTTP source), caches it locally, and exposes its ~18,000 legal concepts through the `FOLIO` API. Any application built on this library therefore consumes and redistributes FOLIO data and must preserve the CC-BY 4.0 attribution below.

FOLIO (Federated Open Legal Information Ontology) is maintained by the **ALEA Institute**, originating from the **SALI Alliance**, licensed **CC-BY 4.0**.

- Source: https://github.com/alea-institute/FOLIO · License: https://creativecommons.org/licenses/by/4.0/

## Notable dependencies

### Runtime (core)

| Component | License | Notes |
|-----------|---------|-------|
| pydantic | MIT | OWL model definitions and validation |
| lxml | BSD-3-Clause | OWL/XML ontology parsing (libxml2/libxslt bindings) |
| httpx | BSD-3-Clause | Fetches ontology from GitHub / HTTP sources |

### Optional (`search` extra)

| Component | License | Notes |
|-----------|---------|-------|
| rapidfuzz | MIT | Fuzzy label matching (degrades gracefully if absent) |
| marisa-trie | MIT AND (BSD-2-Clause OR LGPL-2.1-or-later) | Trie-based prefix search. The Python wrapper is MIT; the bundled `marisa` C++ library is dual-licensed and **we take it under BSD-2-Clause**, which carries no copyleft obligation. |
| alea-llm-client | MIT | Client-agnostic LLM integration for semantic search |

### Dev dependencies

| Component | License |
|-----------|---------|
| types-lxml, ruff, myst-parser | Apache-2.0 / MIT |
| pytest, pytest-benchmark, pytest-cov | MIT |
| pytest-asyncio | Apache-2.0 |
| sphinx, sphinx-book-theme, sphinx-copybutton, sphinxext-opengraph, sphinxcontrib-mermaid, sphinx-plausible | BSD-2-Clause / MIT |
| pylint | GPL-2.0-or-later — a dev-only linter, invoked as a separate process and never imported, linked, or redistributed with this library |

No copyleft obligation attaches to the runtime or `search` dependency sets: the only
dual-licensed component (marisa-trie's C++ core) is taken under its permissive BSD-2-Clause
option, and no GPL/AGPL/EPL dependency is present.
