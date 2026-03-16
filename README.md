# FOLIO Python Library

![FOLIO Logo](docs/_static/folio-logo.png)

[![PyPI version](https://badge.fury.io/py/folio-python.svg)](https://badge.fury.io/py/folio-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/folio-python.svg)](https://pypi.org/project/folio-python/)

The FOLIO Python Library provides a simple and efficient way to interact with the Federated Open Legal Information Ontology (FOLIO).

FOLIO is an open, CC-BY licensed standard designed to represent universal elements of legal data, improving communication and data interoperability across the legal industry.

## Features

- Load the FOLIO ontology from GitHub or a custom HTTP URL
- Search for classes by label or definition
- Query concepts with composable text and structural filters (label, definition, branch, parent, regex, etc.)
- Query properties by label, definition, domain, range, and inverse
- Get subclasses and parent classes
- Access detailed information about each class, including labels, definitions, and examples
- Explore semantic relationships through object properties
- Find connections between entities using labeled relationships
- Analyze property usage, domains, and ranges
- Convert classes to OWL XML, JSON-LD, or Markdown format

## Changelog
The changelog can be found at [CHANGES.md](CHANGES.md).

## Installation

You can install the FOLIO Python library using pip:

```bash
pip install folio-python
```

For search features (fuzzy matching, prefix search, LLM-powered search):

```bash
pip install folio-python[search]
```

> **Note:** The base install includes only `pydantic`, `lxml`, and `httpx`.
> Search features (`search_by_label`, `search_by_definition`, `search_by_prefix`, `query` with fuzzy mode, and LLM search) require the `[search]` extra, which adds `rapidfuzz`, `marisa-trie`, and `alea-llm-client`.

For the latest development version, you can install directly from GitHub:

```bash
pip install --upgrade "folio-python[search] @ https://github.com/alea-institute/folio-python/archive/refs/heads/main.zip"
```

## Quick Start

Here's a simple example to get you started with the FOLIO Python library:

```python
from folio import FOLIO

# Initialize the FOLIO client
folio = FOLIO()

# Search by prefix
results = folio.search_by_prefix("Mich")
for owl_class in results:
    print(f"Class: {owl_class.label}")

# Search for a class by label
results = folio.search_by_label("Mich")
for owl_class, score in results:
    print(f"Class: {owl_class.label}, Score: {score}")

# Get all areas of law
areas_of_law = folio.get_areas_of_law()
for area in areas_of_law:
    print(area.label)

# Working with object properties
properties = folio.get_all_properties()
print(f"Number of object properties: {len(properties)}")

# Get properties by label
drafted_properties = folio.get_properties_by_label("folio:drafted")
for prop in drafted_properties:
    print(f"Property: {prop.label}")
    print(f"Domain: {[folio[d].label for d in prop.domain if folio[d]]}")
    print(f"Range: {[folio[r].label for r in prop.range if folio[r]]}")

# Find connections between entities
connections = folio.find_connections(
    subject_class="https://folio.openlegalstandard.org/R8CdMpOM0RmyrgCCvbpiLS0",  # Actor/Player
    property_name="folio:drafted"
)
for subject, property_obj, object_class in connections:
    print(f"{subject.label} {property_obj.label} {object_class.label}")
```

## Structured Queries

Use `query()` and `query_properties()` for precise, composable filtering:

```python
from folio import FOLIO

folio = FOLIO()

# Find concepts with "trust" in any text field, limited to Area of Law branch
results = folio.query(any_text="trust", branch="AREA_OF_LAW")
for cls in results:
    print(f"{cls.label}: {cls.definition}")

# Regex match on labels
results = folio.query(label="^Contract", match_mode="regex", limit=5)

# Leaf concepts (no children) within a specific parent
results = folio.query(
    parent_iri="RSYBzf149Mi5KE0YtmpUmr",  # Area of Law
    has_children=False,
    limit=10,
)

# Find properties that have an inverse
props = folio.query_properties(has_inverse=True)
for p in props:
    print(f"{p.label} <-> {p.inverse_of}")
```

Match modes: `"substring"` (default), `"exact"`, `"regex"`, `"fuzzy"`

## Searching with an LLM

```python
from folio import FOLIO

# Default: uses gpt-5.1-mini via OpenAI
folio = FOLIO()

# Recommended: gpt-5.4 with low effort and flex tier (1.8s avg, best quality)
folio = FOLIO(effort="low", tier="flex")

# Best value: Grok 4 Fast (1.1s avg, $0.20/M input tokens)
from alea_llm_client import GrokModel
folio = FOLIO(llm=GrokModel(model="grok-4-fast-non-reasoning"))

# Any provider works — effort/tier auto-translate to provider-specific params
from alea_llm_client import GoogleModel
folio = FOLIO(llm=GoogleModel(model="gemini-3-flash-preview"), effort="low")
```

```python
# Search with an LLM
async def search_example():
    for result in await folio.parallel_search_by_llm(
        "redline lease agreement",
        search_sets=[
            folio.get_areas_of_law(max_depth=1),
            folio.get_player_actors(max_depth=2),
        ],
    ):
        print(result)

import asyncio
asyncio.run(search_example())
```

LLM search uses the `alea_llm_client` to provide abstraction across multiple APIs and providers. Requires `pip install folio-python[search]`.

### LLM Benchmark Results

Tested on FOLIO ontology search across 5 legal queries (March 2026):

| Config | Avg Latency | Avg Results | Cost/M input |
|---|---|---|---|
| **grok-4-fast-non-reasoning** | **1.1s** | **4.0** | **$0.20** |
| **gpt-5.4 effort=low tier=flex** | **1.8s** | **3.8** | **$2.50** |
| gemini-3-flash-preview effort=low | 3.6s | 4.8 | low |
| gpt-4.1-mini | 1.7s | 4.0 | $0.40 |

Avoid `effort: "high"` — benchmarks show 5x latency with no quality improvement for structured search tasks.

> **Migrating from soli-python?** The `soli-python` package (v0.1.x) has been renamed to `folio-python`. Uninstall the old package (`pip uninstall soli-python`) and install `folio-python` to avoid dependency conflicts.

## Documentation

For more detailed information about using the FOLIO Python library, please refer to our [full documentation](https://folio-python.readthedocs.io/).

## Contributing

We welcome contributions to the FOLIO Python library! If you'd like to contribute, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and write tests if applicable
4. Run the test suite to ensure everything is working
5. Submit a pull request with a clear description of your changes

For more information, see our [contribution guidelines](CONTRIBUTING.md).

## FOLIO API
A public, freely-accessible API is available for the FOLIO ontology.

The API is hosted at [https://folio.openlegalstandard.org/](https://folio.openlegalstandard.org/).

The source code for the API is available on GitHub at [https://github.com/alea-institute/folio-api](https://github.com/alea-institute/folio-api).


## License

The FOLIO Python library is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions about using the FOLIO Python library, please [open an issue](https://github.com/alea-institute/folio-python/issues) on GitHub.

## Learn More

To learn more about FOLIO, its development, and how you can get involved, visit the [FOLIO website](https://openlegalstandard.org/) or join the [FOLIO community forum](https://discourse.openlegalstandard.org/).
