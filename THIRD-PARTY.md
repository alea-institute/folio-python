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
| marisa-trie | MIT / BSD-2-Clause (dual) | Trie-based prefix search |
| alea-llm-client | MIT | Client-agnostic LLM integration for semantic search |

No copyleft (GPL/AGPL/LGPL/EPL) dependencies are present in the runtime or search dependency sets.
