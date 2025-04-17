# Welcome to the FOLIO Python Documentation

## Introduction

FOLIO (Federated Open Legal Information Ontology) is an open, CC-BY licensed standard designed to represent universal elements of legal data, improving communication and data interoperability across the legal industry.

The FOLIO Python library provides an easy-to-use interface for working with the FOLIO ontology, allowing users to load, parse, and query the FOLIO knowledge graph.

For more information about FOLIO, visit the [official FOLIO website](https://openlegalstandard.org/).

## What is FOLIO?

FOLIO is a comprehensive ontology that includes over 18,000 standardized concepts covering a wide range of legal terms, including both common and specialized concepts. It combines the power of ontology and taxonomy to create a comprehensive way to describe legal information.

Key features of FOLIO include:
- Unique identifiers for every concept
- Multilingual support
- Open development process

## Installation

You can install the FOLIO Python library using `pip` from the following sources:


### GitHub (Development Version)

```bash
pip install --upgrade https://github.com/alea-institute/folio-python/archive/refs/heads/main.zip
```

### PyPI

```bash
pip install folio-python
```

#### Search Extras

**If you want to use the basic search functionality to run fuzzy searches on labels or definitions,
you should install the library with the `[search]` extra:**

```bash
pip install folio-python[search]
```




## Getting Started

Loading the FOLIO ontology is as simple as creating a new FOLIO graph instance:

```python
from folio import FOLIO

# Initialize the FOLIO graph
# This will retrieve the OWL file from the default GitHub repository or
# re-use an existing, cached copy if available.

graph = FOLIO()
```

Once you have initialized the graph, you can conveniently access the FOLIO taxonomy or OWL classes.

```python
print(graph["R8g9E8c4U6pZQefIjUNRuDd"].to_json())
```

```json
{
  "iri": "https://folio.openlegalstandard.org/R8g9E8c4U6pZQefIjUNRuDd",
  "label": "Bankruptcy, Insolvency, and Restructuring Law",
  "sub_class_of": [
    "https://folio.openlegalstandard.org/RSYBzf149Mi5KE0YtmpUmr"
  ],
  "parent_class_of": [
    "https://folio.openlegalstandard.org/R8D2A8vpEW3oEpxLRVkaVDk",
    "https://folio.openlegalstandard.org/RBGaYz0rr5Dh0Sjxu0Z6DHx"
  ],
  "is_defined_by": null,
  "see_also": [],
  "comment": null,
  "deprecated": false,
  "preferred_label": null,
  "alternative_labels": [
    "Bankruptcy and Restructuring",
    "BKCY"
  ],
  "translations": {
    "en-gb": "Bankruptcy and Restructuring Law",
    "pt-br": "Direito de falência e reestruturação",
    "fr-fr": "Droit de la faillite et de la restructuration",
    "de-de": "Insolvenz- und Restrukturierungsrecht",
    "es-es": "Ley de Bancarrota y Reestructuración",
    "es-mx": "Ley de Quiebras y Reestructuración",
    "he-il": "חוקי פשיטת רגל והתארגנות כלכלית",
    "hi-in": "दिवालियापन और पुनर्गठन कानून",
    "zh-cn": "破产和重组法",
    "ja-jp": "破産および再生label"
    :
    "BKCY",
    "definition": "Laws relating to insolvent individuals and companies.",
    "examples": [],
    "notes": [
      "Added \"Insolvency\" to rdfs:label, per UK law (where \"insolvency\" differs from \"bankruptcy\"). In the UK, individuals and companies can be \"insolvent,\" but companies cannot file for \"bankruptcy.\""
    ],
    "history_note": null,
    "editorial_note": null,
    "in_scheme": null,
    "identifier": "BKCY",
    "description": null,
    "source": null,
    "country": null
}
```

### Listing taxonomies

For example, you can list all areas of law in the FOLIO ontology:

```python
# Get all areas of law
areas_of_law = graph.get_areas_of_law()
print(areas_of_law[-1])

# Output: OWLClass(label=Antitrust and Competition Law, iri=https://folio.openlegalstandard.org/RDFwOzDi3E8DQ0OxTKb6UEJ)
````

It's also easy to limit the taxonomic depth:

```python
# Limit to top-level areas of law
areas_of_law = graph.get_areas_of_law()
top_areas_of_law = graph.get_areas_of_law(max_depth=1)
print(f"Count: {len(top_areas_of_law)} / {len(areas_of_law)}")

# Count: 31 / 174
````

Retrieving subgraphs in both directions, e.g., children and parents, is also straightforward:

```python
# Get parent classes for bankruptcy law
print("Parents:", graph.get_parents("R8g9E8c4U6pZQefIjUNRuDd"))

# Get child classes for bankruptcy law
print("Children", graph.get_children("R8g9E8c4U6pZQefIjUNRuDd"))
```

### Working with Object Properties

FOLIO also provides access to object properties, which define relationships between classes:

```python
# Get all object properties
properties = graph.get_all_properties()
print(f"Number of object properties: {len(properties)}")

# Get a specific property
drafted_prop = graph.get_property("https://folio.openlegalstandard.org/R1us3pQhG9zkEb39dZHByB")
print(f"Property: {drafted_prop.label}")

# Find semantic connections between classes
connections = graph.find_connections(
    subject_class="https://folio.openlegalstandard.org/R8CdMpOM0RmyrgCCvbpiLS0",  # Actor/Player
    property_name="folio:drafted"
)

for subject, property_obj, object_class in connections:
    print(f"{subject.label} {property_obj.label} {object_class.label}")
```

### IRIs
Note that you can use the FOLIO IRIs, legacy IRIs, or short-hand identifiers to access classes:

```python
# Get a class by formal IRI
graph["https://folio.openlegalstandard.org/R8g9E8c4U6pZQefIjUNRuDd"] \
    == graph["R8g9E8c4U6pZQefIjUNRuDd"] \
    == graph["http://lmss.sali.org/R8g9E8c4U6pZQefIjUNRuDd"]

# True
```

### Converting classes

Classes can be converted to JSON, OWL, or Markdown in a single line:

 * `.to_json()`: Convert to JSON
 * `.to_owl_element()`: Convert to OWL lxml.etree element
 * `.to_owl_xml()`: Convert to OWL XML string
 * `.to_markdown()`: Convert to rich Markdown string


### Examples

More examples are available in the [examples](examples.md) section.



## Features

- Load the FOLIO ontology from GitHub or a custom HTTP URL
- Search for classes by label or definition
- Get subclasses and parent classes
- Access detailed information about each class, including labels, definitions, and examples
- Explore semantic relationships through object properties
- Find connections between entities using labeled relationships
- Analyze property usage, domains, and ranges
- Convert classes to OWL XML, JSON-LD, or Markdown format

## API Reference

For detailed information about the FOLIO Python library API, please refer to the API documentation (coming soon).

## Contributing

Contributions to the FOLIO Python library are welcome! Please see our [contribution guidelines](https://github.com/alea-institute/folio-python/blob/main/CONTRIBUTING.md) for more information.

## License

The FOLIO Python library is released under the MIT License. See the [LICENSE](https://github.com/alea-institute/folio-python/blob/main/LICENSE) file for details.

The FOLIO standard itself is available under the Creative Commons Attribution (CC-BY) License.

```{toctree}
:maxdepth: 2
:caption: Contents:

examples
folio/graph
folio/models
folio/config
folio/logger
```

## Indices and Tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`

## Learn More

To learn more about FOLIO, its development, and how you can get involved, visit the [FOLIO website](https://openlegalstandard.org/) or join the [FOLIO community forum](https://openlegalstandard.org/forum/).