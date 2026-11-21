"""Run the expanded-search example with local RDF and a stub LLM only."""

import importlib.util
import json
from pathlib import Path

import httpx
import pytest

from folio import FOLIO


BASE = "https://folio.openlegalstandard.org/"
HABITABILITY = BASE + "RHabitability"
LANDLORD = BASE + "RLandlord"
NEGLIGENCE = BASE + "RNegligence"
EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples/expanded_search.py"


def load_example():
    spec = importlib.util.spec_from_file_location("expanded_search", EXAMPLE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def unexpected_request(*args, **kwargs):
        pytest.fail("The example test must not make network requests")

    monkeypatch.setattr(httpx.Client, "send", unexpected_request)
    monkeypatch.setattr(httpx.AsyncClient, "send", unexpected_request)
    monkeypatch.setenv("FOLIO_SEARCH_BACKEND", "rapidfuzz")


@pytest.fixture
def example():
    return load_example()


@pytest.fixture
def graph(local_graph):
    return local_graph(f'''
        <owl:Class rdf:about="{HABITABILITY}">
            <rdfs:label>Warranty of Habitability</rdfs:label>
            <skos:definition>Tenant rights to a habitable home.</skos:definition>
        </owl:Class>
        <owl:Class rdf:about="{LANDLORD}">
            <rdfs:label>Landlord</rdfs:label>
            <skos:definition>The owner of a rental home.</skos:definition>
        </owl:Class>
        <owl:Class rdf:about="{NEGLIGENCE}">
            <rdfs:label>Landlord Negligence</rdfs:label>
            <skos:definition>A landlord's failure to maintain a rental home.</skos:definition>
        </owl:Class>
    ''')


def test_example_import_does_not_construct_graph(monkeypatch):
    def unexpected_init(*args, **kwargs):
        pytest.fail("Importing the example must not construct a graph")

    monkeypatch.setattr(FOLIO, "__init__", unexpected_init)
    assert callable(load_example().expanded_search)


@pytest.mark.asyncio
async def test_example_expands_query_offline(example, graph):
    class CountingDemoLLM(example.DemoLLM):
        calls = 0

        async def json_async(self, prompt, **kwargs):
            self.calls += 1
            return await super().json_async(prompt, **kwargs)

    graph.llm = CountingDemoLLM()
    result = await example.expanded_search(
        graph,
        "my landlord won't fix the heat",
        limit=3,
        include_definitions=True,
        max_expansions=8,
        timeout=10.0,
    )

    assert graph.llm.calls == 1
    assert result.query == "my landlord won't fix the heat"
    assert result.expansion_source == "llm"
    assert result.expansions == ["Warranty of Habitability", "Landlord Negligence"]
    assert len(result.hits) == 3
    by_iri = {hit.owl_class.iri: hit for hit in result.hits}
    assert "Warranty of Habitability" in by_iri[HABITABILITY].matched_via
    assert "Landlord Negligence" in by_iri[NEGLIGENCE].matched_via
    assert result.expansion_error is None

    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["expansion_source"] == "llm"
    assert payload["expansions"] == result.expansions
    assert "hits" not in payload
    assert "usage" not in payload
    assert len(payload["results"]) == 3
    for row, hit in zip(payload["results"], result.hits):
        assert row == {
            "iri": hit.owl_class.iri,
            "label": hit.owl_class.label,
            "score": hit.score,
            "matched_via": hit.matched_via,
        }


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_unavailable", [True, False])
async def test_example_falls_back_to_plain_search(example, graph, provider_unavailable):
    class FailingLLM:
        async def json_async(self, prompt, **kwargs):
            raise RuntimeError("Demo provider unavailable")

    graph.llm = None if provider_unavailable else FailingLLM()
    result = await example.expanded_search(
        graph, "Landlord", limit=2, include_definitions=False
    )
    plain = graph.search_by_label("Landlord", limit=10)[:2]

    assert result.expansion_source == "none"
    assert result.expansions == []
    assert result.hits[0].owl_class.iri == LANDLORD
    assert [hit.owl_class.iri for hit in result.hits] == [
        owl_class.iri for owl_class, _ in plain
    ]
    assert all(hit.matched_via == ["Landlord"] for hit in result.hits)


@pytest.mark.asyncio
async def test_example_can_disable_expansion(example, graph):
    class UnexpectedLLM:
        async def json_async(self, prompt, **kwargs):
            pytest.fail("max_expansions=0 must not call the LLM")

    graph.llm = UnexpectedLLM()
    result = await example.expanded_search(
        graph, "Landlord", include_definitions=False, max_expansions=0
    )

    assert result.hits[0].owl_class.iri == LANDLORD
    assert result.expansion_source == "none"
    assert result.expansions == []
