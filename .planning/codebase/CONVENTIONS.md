# Coding Conventions

**Analysis Date:** 2026-04-07

## Naming Patterns

**Files:**
- Module files use lowercase with underscores: `graph.py`, `models.py`, `logger.py`, `config.py`
- Example files use lowercase with underscores describing functionality: `basic_taxonomy.py`, `initialize_client.py`, `property_categories.py`

**Classes:**
- Use PascalCase: `FOLIO`, `OWLClass`, `OWLObjectProperty`, `FOLIOConfiguration`, `FOLIOTypes`
- Enum members use UPPER_CASE_WITH_UNDERSCORES: `ACTOR_PLAYER`, `AREA_OF_LAW`, `ASSET_TYPE`

**Functions and Methods:**
- Use snake_case: `get_logger()`, `load_owl_github()`, `search_by_label()`, `to_markdown()`, `is_valid()`
- Conversion methods use `to_*()` pattern: `to_owl_element()`, `to_owl_xml()`, `to_json()`, `to_jsonld()`, `to_markdown()`
- Factory methods use `from_*()` pattern: `from_json()`
- Getter methods use `get_*()` pattern: `get_logger()`, `get_types()`, `get_property()`, `get_triples_by_predicate()`
- Filter/search methods use `search_*()` pattern: `search_by_prefix()`, `search_by_label()`, `search_by_definition()`

**Variables and Attributes:**
- Use snake_case for attributes and local variables: `source_type`, `http_url`, `github_repo_owner`, `cache_path`, `iri_to_index`
- Dictionary keys use lowercase with underscores: `"folio"`, `"repo_owner"`, `"use_cache"`
- Private/internal attributes do not use underscore prefix in Pydantic models (Field definitions)

**Type Hints:**
- Always use type hints for function parameters and return types: `def get_logger(name: str) -> logging.Logger:`
- Use Python 3.10+ union syntax with `|` where appropriate: `str | Path`, `Optional[str]`, `Dict[str, int]`
- Use forward references for self-referencing types: `from __future__ import annotations`
- Generic types use fully qualified names: `Dict`, `List`, `Optional`, `Tuple`, `Literal`

## Code Style

**Formatting:**
- Line length: 120 characters max (configured in `pyproject.toml`)
- Formatter: `black` and `ruff` (via pre-commit hooks)
- Indentation: 4 spaces

**Linting:**
- Primary linter: `pylint` configured in `pyproject.toml`
- Pre-commit hooks: `ruff` (check --fix), `ruff-format`, `pre-commit-hooks`
- pylint disabled rules: `line-too-long`, `too-few-public-methods`, `no-self-argument`, `cyclic-import`
- File-level pylint directives used: `# pylint: disable=fixme,no-member,unsupported-assignment-operation,too-many-lines,too-many-public-methods,invalid-name`

## Import Organization

**Order:**
1. Standard library imports (`sys`, `asyncio`, `json`, `logging`, `pathlib`, etc.)
2. Third-party imports (`pydantic`, `lxml`, `httpx`, etc.)
3. Project imports (`from folio import...`, `from folio.logger import...`)

**Example from `folio/graph.py`:**
```python
# future import for self-referencing type hints
from __future__ import annotations

# imports
import asyncio
import base64
import hashlib
import importlib.util
import json
import time
import traceback
import uuid
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

# packages
import httpx
import lxml.etree
from alea_llm_client import BaseAIModel

# project imports
from folio.config import (...)
from folio.logger import get_logger
from folio.models import OWLClass, OWLObjectProperty, NSMAP
```

**Path Aliases:**
- Not used; imports are explicit with relative module names
- Configuration imports from `folio.config`, logging from `folio.logger`, models from `folio.models`

## Docstrings

**Format:** Google-style docstrings for all public classes and methods

**Class docstrings:**
```python
class OWLClass(BaseModel):
    """
    OWLClass model for the FOLIO package, which represents an OWL class in the FOLIO
    ontology/taxonomy style.

    TODO: think about future-proofing for next-gen roadmap.
    """
```

**Method docstrings:**
```python
def is_valid(self) -> bool:
    """
    Check if the OWL class is valid.

    Returns:
        bool: True if the OWL class is valid, False otherwise.
    """
    return self.label is not None
```

**Function docstrings with arguments:**
```python
@staticmethod
def load_owl(
    source_type: str = DEFAULT_SOURCE_TYPE,
    http_url: Optional[str] = DEFAULT_HTTP_URL,
    github_repo_owner: str = DEFAULT_GITHUB_REPO_OWNER,
    github_repo_name: str = DEFAULT_GITHUB_REPO_NAME,
    github_repo_branch: str = DEFAULT_GITHUB_REPO_BRANCH,
    use_cache: bool = True,
) -> str:
    """
    Load the FOLIO ontology in OWL format.

    Args:
        source_type (str): The source type for loading the ontology. Either "github" or "http".
        http_url (Optional[str]): The HTTP URL for the ontology.
        github_repo_owner (str): The owner of the GitHub repository.
        github_repo_name (str): The name of the GitHub repository.
        github_repo_branch (str): The branch of the GitHub repository.
        use_cache (bool): Whether to use the local cache.
    """
```

## Comments

**When to Comment:**
- Explain "why" not "what" — code that is self-documenting via clear naming does not need comments
- Use comments for complex logic, non-obvious decisions, or important caveats
- Include comments for workarounds or temporary solutions

**Example from `folio/models.py`:**
```python
# We no longer need to handle seeAlso restrictions separately since all seeAlso
# relationships are now in the main see_also list

# add the label element
label_element = lxml.etree.Element(f"{{{NSMAP['rdfs']}}}label", nsmap=NSMAP)
```

**TODO/FIXME markers:**
- Used to mark incomplete work: `TODO: think about future-proofing for next-gen roadmap.`
- Used to mark needed implementations: `TODO: implement token caching layer in system prompt for search`
- Flagged by pylint with `fixme` disabled to allow checking

## Module Constants

**Configuration constants:** Defined at module level in `config.py` with `DEFAULT_` prefix
```python
DEFAULT_CACHE_DIR: Path = Path.home() / ".folio" / "cache"
DEFAULT_MAX_DEPTH: int = 16
MAX_IRI_ATTEMPTS: int = 16
DEFAULT_MAX_TOKENS: int = 1024
```

**Module-level dictionaries:** Use UPPER_CASE for enums and mappings
```python
FOLIO_TYPE_IRIS = {
    FOLIOTypes.ACTOR_PLAYER: "R8CdMpOM0RmyrgCCvbpiLS0",
    FOLIOTypes.AREA_OF_LAW: "RSYBzf149Mi5KE0YtmpUmr",
    ...
}

NSMAP = {
    None: "https://folio.openlegalstandard.org/",
    "dc": "http://purl.org/dc/elements/1.1/",
    ...
}
```

## Data Validation

**Framework:** Pydantic v2 for all data models

**Usage:** `BaseModel` for structured data with Field descriptors for documentation
```python
class OWLClass(BaseModel):
    iri: str = Field(..., description="{http://www.w3.org/2002/07/owl#}Class")
    label: Optional[str] = Field(
        None, description="{http://www.w3.org/2000/01/rdf-schema#}label"
    )
    sub_class_of: List[str] = Field(
        default_factory=list,
        description="{http://www.w3.org/2000/01/rdf-schema#}subClassOf",
    )
```

**Validation methods:** Use `model_validate()` and `model_validate_json()` from Pydantic
```python
@classmethod
def from_json(cls, json_string: str) -> "OWLClass":
    return cls.model_validate_json(json_string)
```

## Error Handling

**Pattern:** Raise specific exception types with context-rich messages

**For external API errors:**
```python
try:
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        branches = response.json()
        return [branch["name"] for branch in branches]
except httpx.HTTPStatusError as e:
    raise RuntimeError(
        f"Error listing branches for {repo_owner}/{repo_name}"
    ) from e
```

**For validation errors:**
```python
if source_type == "github":
    cache_key = f"{github_repo_owner}/{github_repo_name}/{github_repo_branch}"
elif source_type == "http":
    if http_url is None:
        raise ValueError("HTTP URL must be provided for source type 'http'.")
    cache_key = http_url
else:
    raise ValueError("Invalid source type. Must be either 'github' or 'http'.")
```

**For import errors:** Graceful handling with logging warnings
```python
try:
    if importlib.util.find_spec("rapidfuzz") is not None:
        import rapidfuzz
    else:
        LOGGER.warning("Disabling search functionality: rapidfuzz not found.")
        rapidfuzz = None
except ImportError as e:
    LOGGER.warning("Failed to check for search functionality: %s", e)
    rapidfuzz = None
```

**For broad exception handling:** Only when appropriate, marked with `# pylint: disable=broad-except`
```python
try:
    if llm is None:
        self.llm = alea_llm_client.OpenAIModel(model="gpt-4o")
    else:
        self.llm = llm
    LOGGER.info("Initialized LLM model: %s", self.llm)
except Exception:  # pylint: disable=broad-except
    LOGGER.warning(
        "Failed to initialize LLM model: %s", traceback.format_exc()
    )
```

## Logging

**Framework:** Standard library `logging` module via `get_logger()` utility

**Usage:** `LOGGER = get_logger(__name__)` at module level in `folio/logger.py`

**Log levels:**
- `LOGGER.warning()` for optional features that could not be enabled or recoverable issues
- `LOGGER.info()` for significant operations (loading ontology, parsing, initialization)
- Default level: WARNING (set in `folio/logger.py`)

**Patterns:**
```python
LOGGER.info("Loading FOLIO ontology from %s...", source_type)
LOGGER.info("Parsed FOLIO ontology in %.2f seconds", end_time - start_time)
LOGGER.warning("Disabling search functionality: rapidfuzz not found.")
```

## Function Design

**Size:** Methods can be longer (50-200 lines) when parsing complex XML or building data structures

**Parameters:**
- Use keyword arguments for better readability with multiple parameters
- Provide reasonable defaults for optional parameters: `use_cache: bool = True`
- Use static methods for utility functions not requiring instance state: `@staticmethod def list_branches(...)`

**Return Values:**
- Always include return type hint
- Return `None` explicitly when appropriate: `-> None`
- Return typed collections: `-> List[str]`, `-> Dict[str, int]`, `-> Optional[str]`
- Methods that return another class instance use the class name in quotes for forward references

**Example from `folio/graph.py`:**
```python
@staticmethod
def load_owl_github(
    repo_owner: str = DEFAULT_GITHUB_REPO_OWNER,
    repo_name: str = DEFAULT_GITHUB_REPO_NAME,
    repo_branch: str = DEFAULT_GITHUB_REPO_BRANCH,
) -> str:
    """Load the FOLIO ontology in OWL format from a GitHub repository."""
    # GitHub URL for the ontology file
    url = f"{DEFAULT_GITHUB_OBJECT_URL}/{repo_owner}/{repo_name}/{repo_branch}/FOLIO.owl"
    try:
        with httpx.Client() as client:
            LOGGER.info(
                "Loading ontology from %s/%s/%s", repo_owner, repo_name, repo_branch
            )
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        raise RuntimeError(...) from e
```

## Module Design

**Exports:** Explicit `__all__` in `folio/__init__.py` for public API
```python
__all__ = [
    "FOLIO",
    "FOLIOTypes",
    "FOLIO_TYPE_IRIS",
    "OWLClass",
    "OWLObjectProperty",
    "NSMAP",
]
```

**Barrel Files:** Not used; imports are from specific modules

**Module organization:**
- `folio/__init__.py` — Package exports and version metadata
- `folio/graph.py` — Main FOLIO class and FOLIOTypes enum
- `folio/models.py` — OWLClass, OWLObjectProperty, NSMAP definitions
- `folio/config.py` — Configuration management and defaults
- `folio/logger.py` — Logging utility

## Class Design

**BaseModel usage:** All data structures inherit from Pydantic `BaseModel`
- Provides validation, serialization (`model_dump()`, `model_dump_json()`)
- Field descriptors document each attribute with SKOS/RDF semantics

**Instance attributes initialized in `__init__`:**
```python
self.source_type: str = source_type
self.http_url: Optional[str] = http_url
self.tree: Optional[lxml.etree._Element] = None
self.classes: List[OWLClass] = []
self.iri_to_index: Dict[str, int] = {}
```

**Lazy initialization of optional features:**
```python
self.llm: Optional[BaseAIModel] = None
if alea_llm_client is not None:
    try:
        if llm is None:
            self.llm = alea_llm_client.OpenAIModel(model="gpt-4o")
        else:
            self.llm = llm
    except Exception:
        LOGGER.warning(...)
```

---

*Convention analysis: 2026-04-07*
