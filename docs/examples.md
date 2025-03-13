# FOLIO Python Examples

This document provides examples of how to use the FOLIO (Federated Open Legal Information Ontology) Python library. We'll start with basic usage and progress to more complex examples.

## Installation

You can install the latest version of the FOLIO Python library from GitHub using `pip`:

```bash
pip install --upgrade https://github.com/alea-institute/folio-python/archive/refs/heads/main.zip
```

## Initializing the FOLIO Graph

```python
from folio import FOLIO

# Initialize the FOLIO graph with default settings
folio = FOLIO()

# Initialize with custom settings
folio_custom = FOLIO(
    source_type="github",
    github_repo_owner="alea-institute",
    github_repo_name="FOLIO",
    github_repo_branch="1.0.0",
    use_cache=True
)

# Initialize from a custom HTTP URL
folio_http = FOLIO(
    source_type="http",
    http_url="https://github.com/alea-institute/FOLIO/raw/main/FOLIO.owl"
)
```

## Basic Operations

```python
# Get the number of classes in the ontology
print(f"Number of classes: {len(folio)}")

# Get ontology title and description
print(f"Title: {folio.title}")
print(f"Description: {folio.description}")

# Access a class by IRI
contract_class = folio["https://folio.openlegalstandard.org/R602916B1A80fDD28d392d3f"]
print(f"Class: {contract_class.label}")
print(f"Definition: {contract_class.definition}")

# Access a class by short IRI
edmi_class = folio["R602916B1A80fDD28d392d3f"]
print(f"Class: {edmi_class.label}")

# Get class by index
first_class = folio[0]
print(f"First class: {first_class.label}")
```

## Searching for Classes

### Search by Label

**Make sure that you have installed with the `[search]` extra to use the search functionality. See the [installation instructions](index.md#search-extras).**


```python
# Search for classes with "SDNY" in the label
results = folio.search_by_label("SDNY", limit=3)
for owl_class, score in results:
    print(f"Class: {owl_class.label}, Score: {score}")
```

### Search by Definition

```python
# Search for classes with "waterways" in the definition
results = folio.search_by_definition("waterways", limit=3)
print("** Definitions **")
for owl_class, score in results:
    print(f"Class: {owl_class.label}, Definition: {owl_class.definition[:50]}..., Score: {score}")
```

## Working with FOLIO Taxonomic Types

```python
from folio import FOLIOTypes

# Get all areas of law
areas_of_law = folio.get_areas_of_law()
print("Areas of Law:")
for area in areas_of_law:
    print(f"- {area.label}")

# Get all legal entities
legal_entities = folio.get_legal_entities()
print("\nLegal Entities:")
for entity in legal_entities:
    print(f"- {entity.label}")

# Get all industries
industries = folio.get_industries()
print("\nIndustries:")
for industry in industries:
    print(f"- {industry.label}")
```

## Traversing the Ontology

```python
# Get parent classes
bankruptcy_law = folio.search_by_label("Personal Bankruptcy Law")[0][0]
parent_classes = folio.get_parents(bankruptcy_law.iri)
print("Parent classes of Personal Bankruptcy Law:")
for parent in parent_classes:
    print(f"- {parent.label}")

# Get child classes
area_of_law_iri = folio["https://folio.openlegalstandard.org/RSYBzf149Mi5KE0YtmpUmr"].iri
child_classes = folio.get_children(area_of_law_iri, max_depth=1)
print("\nDirect child classes of Area of Law:")
for child in child_classes:
    print(f"- {child.label}")

# Get entire subgraph
subgraph = folio.get_subgraph(area_of_law_iri, max_depth=2)
print(f"\nNumber of classes in Area of Law subgraph (depth 2): {len(subgraph)}")
```

## Working with Triples

```python
# Get triples by predicate
is_defined_by_triples = folio.get_triples_by_predicate("rdfs:isDefinedBy")
print(f"Number of rdfs:isDefinedBy triples: {len(is_defined_by_triples)}")

# Get triples by subject
subject_iri = "https://folio.openlegalstandard.org/RBGPkZ1oRgcP05LWQBGLEne"
subject_triples = folio.get_triples_by_subject(subject_iri)
print(f"\nTriples for subject {subject_iri}:")
for triple in subject_triples:
    print(f"- {triple[1]} {triple[2]}")

# Get triples by object
object_iri = "https://folio.openlegalstandard.org/R9sbuHkJC9aqDlHAgw58VSB"
object_triples = folio.get_triples_by_object(object_iri)
print(f"\nTriples with object {object_iri}:")
for triple in object_triples:
    print(f"- {triple[0]} {triple[1]}")
```

## Advanced Usage

### Refreshing the Ontology

```python
# Refresh the ontology to get the latest version
folio.refresh()
print(f"Ontology refreshed. New class count: {len(folio)}")
```

### Generating New IRIs

```python
# Generate a new IRI for a custom class
new_iri = folio.generate_iri()
print(f"Generated IRI: {new_iri}")
```

### Working with Multiple Branches

```python
# List available branches
branches = FOLIO.list_branches()
print("Available branches:")
for branch in branches:
    print(f"- {branch}")

# Load a specific branch
folio_1_0_0 = FOLIO(github_repo_branch="1.0.0")
print(f"Loaded FOLIO version 1.0.0. Class count: {len(folio_1_0_0)}")
```

These examples demonstrate the basic and advanced usage of the FOLIO Python library. You can explore more functionality by referring to the API documentation and the source code of the `FOLIO` class in the `folio/graph.py` file.