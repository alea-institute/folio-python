"""Optional fuzzy search must handle sparse inputs and absent extras."""

import pytest

import folio.graph


IRI = "https://folio.openlegalstandard.org/Rcontract"
CLASS = (
    f'<owl:Class rdf:about="{IRI}"><rdfs:label>Contract</rdfs:label>{{}}</owl:Class>'
)


@pytest.mark.parametrize("contents", ["", CLASS.format("")])
def test_empty_definition_corpus(local_graph, contents):
    # The development environment must exercise actual RapidFuzz, not silently skip it.
    import rapidfuzz

    assert folio.graph.rapidfuzz is rapidfuzz
    assert local_graph(contents).search_by_definition("contract") == []


def test_populated_definition_corpus(local_graph):
    graph = local_graph(
        CLASS.format("<skos:definition>A binding agreement</skos:definition>")
    )
    results = graph.search_by_definition("binding agreement", limit=1)
    assert len(results) == 1
    assert results[0][0].iri == IRI
    assert results[0][1] > 90


@pytest.mark.parametrize(
    "contents", ["", CLASS.format("<skos:definition>Agreement</skos:definition>")]
)
def test_missing_rapidfuzz_errors_even_for_empty_corpus(
    local_graph, monkeypatch, contents
):
    graph = local_graph(contents)
    monkeypatch.setattr(folio.graph, "rapidfuzz", None)
    for search in (graph.search_by_label, graph.search_by_definition):
        with pytest.raises(RuntimeError, match="search extra must be installed"):
            search("contract")


def test_python_prefix_and_structured_text_without_search(local_graph, monkeypatch):
    monkeypatch.setattr(folio.graph, "marisa_trie", None)
    monkeypatch.setattr(folio.graph, "rapidfuzz", None)
    graph = local_graph(CLASS.format("<skos:altLabel>Agreement</skos:altLabel>"))
    assert [c.iri for c in graph.search_by_prefix("CON")] == [IRI]
    assert [c.iri for c in graph.search_by_prefix("Agr", case_sensitive=True)] == [IRI]
    assert [c.iri for c in graph.query(label="Contract", match_mode="exact")] == [IRI]
    assert [c.iri for c in graph.query(label="tract", match_mode="substring")] == [IRI]
