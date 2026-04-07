# Testing Patterns

**Analysis Date:** 2026-04-07

## Test Framework

**Runner:**
- `pytest` 8.3.1 - 8.x (configured in `pyproject.toml`)
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`

**Assertion Library:**
- Standard `assert` statements (no dedicated assertion library)

**Coverage:**
- `pytest-cov` 5.0.0 - 5.x
- Coverage output: `--cov=folio --cov-report=term-missing --cov-report=xml --cov-report=html`
- Coverage file: `coverage.xml` and HTML report in `htmlcov/`

**Additional Frameworks:**
- `pytest-asyncio` 0.23.8 - 0.24.x for async test support
- `pytest-benchmark` 4.0.0 - 5.x for performance benchmarking

**Run Commands:**
```bash
# Run all tests with coverage
pytest

# Run tests with coverage reports (term, xml, html)
pytest --cov=folio --cov-report=term-missing --cov-report=xml --cov-report=html

# Run specific test file
pytest tests/test_folio.py

# Run with verbose output
pytest -v

# Run with markers
pytest -m marker_name
```

## Test File Organization

**Location:** `tests/` directory at project root

**Naming:** `test_*.py` pattern
- Single test file: `tests/test_folio.py` (comprehensive test suite)

**Test file structure:** Module-level fixture definition followed by individual test functions

## Test Structure

**Fixture Definition:**
```python
@pytest.fixture(scope="module")
def folio_graph():
    return FOLIO()
```

**Test Functions:**
- Named with `test_` prefix: `test_list_branches()`, `test_load_owl()`, `test_class_get()`
- Docstrings describe test purpose
- Use fixture parameters to access shared resources: `def test_class_count(folio_graph):`

**Test Organization Pattern from `tests/test_folio.py`:**

1. **Fixture Definition** (module-level, scope="module")
   ```python
   @pytest.fixture(scope="module")
   def folio_graph():
       return FOLIO()
   ```

2. **Static Method Tests** (no fixture needed)
   ```python
   def test_list_branches():
       """Test the list_branches method of the FOLIO class."""
       branches = FOLIO.list_branches()
       assert isinstance(branches, list)
       assert len(branches) > 1
       assert "main" in branches
   ```

3. **Initialization Tests** (testing different constructor paths)
   ```python
   def test_load_owl_nocache():
       """Test the load_owl method of the FOLIO class with the default GitHub repository."""
       ontology = FOLIO(use_cache=False)
       assert ontology is not None
       assert len(ontology) > 0
   ```

4. **Instance Method Tests** (using fixture)
   ```python
   def test_class_get(folio_graph):
       """Test getting a class from the graph."""
       edmi = folio_graph["https://folio.openlegalstandard.org/R602916B1A80fDD28d392d3f"]
       assert edmi is not None
       assert isinstance(edmi, OWLClass)
   ```

5. **Error Case Tests** (using `pytest.raises`)
   ```python
   def test_list_branches_bad():
       """Test the list_branches method of the FOLIO class."""
       with pytest.raises(Exception):
           branches = FOLIO.list_branches(repo_owner="alea-institute-wrong-name")
   ```

## Mocking

**Framework:** Not explicitly used in current test suite

**Patterns:** Tests use real external resources (GitHub API, HTTP downloads)
- Network calls are made to GitHub and raw content URLs
- Tests assume network connectivity and valid external resources
- No mock objects or patch decorators observed

**Alternative approach for isolated testing:**
- Could use `unittest.mock.patch()` for network isolation
- Could use `responses` library for HTTP mocking
- Currently, tests validate actual integration with external services

## Fixtures

**Test Data:**
- Tests use real FOLIO ontology data from GitHub
- IRIs used: `"https://folio.openlegalstandard.org/R602916B1A80fDD28d392d3f"` (U.S. District Court - W.D. Michigan)
- Fixture scope: `"module"` - shared across all test functions in the file

**Fixture usage:**
```python
# Define fixture
@pytest.fixture(scope="module")
def folio_graph():
    return FOLIO()

# Use in tests
def test_class_count(folio_graph):
    assert len(folio_graph.classes) > 18000

def test_class_get(folio_graph):
    edmi = folio_graph["R602916B1A80fDD28d392d3f"]
    assert edmi is not None
```

## Test Coverage

**Current Coverage:**
- ~50% of code covered (based on `coverage.xml` present)
- Coverage reports generated in multiple formats: terminal, XML, HTML

**Areas Tested:**
1. Ontology loading from multiple sources (GitHub, HTTP, cache)
2. Data model conversion (to_markdown, to_json, to_jsonld, to_owl_xml)
3. Search functionality (search_by_prefix, search_by_label, search_by_definition)
4. Type retrieval methods (get_player_actors, get_areas_of_law, etc.)
5. Triple handling and queries
6. Object properties and connections
7. seeAlso relations

**Test File Statistics:**
- Total lines: ~400
- Number of test functions: ~30
- Mix of unit and integration tests

## Test Examples

**Successful Load Test:**
```python
def test_load_owl_github():
    """Test the load_owl method of the FOLIO class with the default GitHub repository."""
    ontology = FOLIO.load_owl_github()
    assert ontology is not None
    assert len(ontology) > 0
    assert "owl:Ontology" in ontology
```

**Data Retrieval Test:**
```python
def test_class_get(folio_graph):
    # test a good class by iri
    edmi = folio_graph["https://folio.openlegalstandard.org/R602916B1A80fDD28d392d3f"]
    assert edmi is not None
    assert isinstance(edmi, OWLClass)

    # get by just iri suffix
    edmi = folio_graph["R602916B1A80fDD28d392d3f"]
    assert edmi is not None
    assert isinstance(edmi, OWLClass)

    # get with prefixes
    edmi = folio_graph["folio:R602916B1A80fDD28d392d3f"]
    assert edmi is not None
    assert isinstance(edmi, OWLClass)
```

**Search Functionality Test:**
```python
def test_search_label(folio_graph):
    for c, score in folio_graph.search_by_label("Georgia"):
        assert "Georgia" in c.label
        assert "US+GA" in c.alternative_labels
        assert score > 0.9
        break

    for c, score in folio_graph.search_by_label("SDNY"):
        assert c.label == "U.S. District Court - S.D. New York"
        assert "S.D.N.Y." in c.alternative_labels
        assert score > 0.9
        break
```

**Error Handling Test:**
```python
def test_load_owl_bad_http():
    """Test the load_owl method of the FOLIO class with the default HTTP URL."""
    with pytest.raises(Exception):
        FOLIO.load_owl_http(
            http_url="https://github.com/alea-institute/FOLIO/raw/main/FOLIO.wol"
        )
```

**Property and Connection Test:**
```python
def test_object_properties(folio_graph):
    """Test that object properties are properly parsed from the OWL file."""
    assert len(folio_graph.object_properties) > 0
    
    test_property = folio_graph.get_property("https://folio.openlegalstandard.org/R0q5hTo2yTMlnIAbmFnwCH")
    assert test_property is not None
    assert test_property.label == "hasFigure"
    
    opposed_props = folio_graph.get_properties_by_label("folio:opposed")
    assert len(opposed_props) > 0
    for prop in opposed_props:
        assert "opposed" in prop.label or "opposed" in prop.alternative_labels
```

## Test Async Patterns

**Framework:** `pytest-asyncio` available but not currently used in test suite

**Pattern if needed:**
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

## Test Performance

**Benchmarking:**
- `pytest-benchmark` available in dev dependencies
- Can be used to track performance regressions
- Usage: `@pytest.mark.benchmark` decorator on test functions

**Long-running tests:**
- Ontology loading tests may take several seconds
- Module-scoped fixture reduces repeat initialization overhead
- Cache directory at `~/.folio/cache/` stores downloaded ontologies

## Test Types Observed

**Unit Tests:**
- Data model validation: `test_class_json()`, `test_class_jsonld()`
- Format conversion: `test_class_markdown()`, `test_class_xml()`
- Scope: Individual class/method functionality

**Integration Tests:**
- Full ontology loading: `test_load_owl()`, `test_load_owl_github()`
- External API integration: `test_list_branches()`, `test_load_owl_http()`
- Search across entire dataset: `test_search_label()`, `test_search_definitions()`
- Scope: System-wide functionality, real external dependencies

**Data Integrity Tests:**
- Verify ontology structure: `test_class_count()` (asserts >18000 classes)
- Verify relationships: `test_object_properties()`, `test_see_also_relations()`
- Verify triple consistency: `test_triples()`

## E2E Tests

**Not Explicitly Defined:**
- Integration tests serve as end-to-end validation
- Full ontology lifecycle tested: load → parse → query → convert
- External dependencies (GitHub) are part of test execution

## Running Tests

**Command to run all tests:**
```bash
pytest
```

**With coverage report:**
```bash
pytest --cov=folio --cov-report=term-missing --cov-report=xml --cov-report=html
```

**View HTML coverage:**
```bash
# Report generated in htmlcov/index.html
open htmlcov/index.html
```

**Run specific test:**
```bash
pytest tests/test_folio.py::test_class_get -v
```

**Run tests with output:**
```bash
pytest -v --tb=short
```

## Known Test Considerations

**Test Dependencies:**
- Network access required for GitHub API and raw content downloads
- Tests will fail without internet connectivity
- External API stability required (GitHub uptime)

**Cache Behavior:**
- Tests can be run with `use_cache=False` to bypass caching
- Cached ontologies stored in `~/.folio/cache/` directory
- Tests may be faster on second run due to caching

**Test Data:**
- Uses real FOLIO ontology (2.0.0 branch default)
- IRI references in tests must match actual ontology data
- Tests brittle to ontology changes (hardcoded IRIs and labels)

---

*Testing analysis: 2026-04-07*
