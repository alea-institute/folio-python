# FOLIO Python Library

![FOLIO Logo](https://openlegalstandard.org/assets/images/folio-intro-logo.png)

[![PyPI version](https://badge.fury.io/py/folio-python.svg)](https://badge.fury.io/py/folio-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/folio-python.svg)](https://pypi.org/project/folio-python/)

The FOLIO Python Library provides a simple and efficient way to interact with the Federated Open Legal Information Ontology (FOLIO).

FOLIO is an open, CC-BY licensed standard designed to represent universal elements of legal data, improving communication and data interoperability across the legal industry.

## Features

- Load the FOLIO ontology from GitHub or a custom HTTP URL
- Search for classes by label or definition
- Get subclasses and parent classes
- Access detailed information about each class, including labels, definitions, and examples
- Convert classes to OWL XML or Markdown format

## Changelog
The changelog can be found at [CHANGES.md](CHANGES.md).

## Installation

You can install the FOLIO Python library using pip:

```bash
pip install folio-python
```

For the latest development version, you can install directly from GitHub:

```bash
pip install --upgrade https://github.com/alea-institute/folio-python/archive/refs/heads/main.zip
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
```

## Searching with an LLM

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

LLM search uses the `alea_llm_client` to provide abstraction across multiple APIs and providers.

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
