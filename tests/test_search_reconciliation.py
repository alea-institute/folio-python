"""Deterministic parser-to-search regressions for the reconciled search branches."""

import importlib

import pytest

import folio.graph
from folio import FOLIO


ROAD_IRI = "https://folio.openlegalstandard.org/Rroad"
PRIMARY_IRI = "https://folio.openlegalstandard.org/Rprimary"
ALTERNATIVE_IRI = "https://folio.openlegalstandard.org/Ralternative"


def owl_document(classes):
    return f"""<rdf:RDF
        xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
        xmlns:owl="http://www.w3.org/2002/07/owl#"
        xmlns:skos="http://www.w3.org/2004/02/skos/core#">
        {classes}
    </rdf:RDF>"""


@pytest.fixture(params=["marisa", "python"])
def load_graph(request, monkeypatch):
    # An unavailable MARISA dependency must fail its cases, not silently use fallback.
    backend = (
        importlib.import_module("marisa_trie") if request.param == "marisa" else None
    )
    monkeypatch.setattr(folio.graph, "marisa_trie", backend)
    monkeypatch.setattr(folio.graph, "alea_llm_client", None)

    def load(*documents):
        buffers = iter(documents)

        def load_owl(*args, **kwargs):
            return next(buffers)

        monkeypatch.setattr(FOLIO, "load_owl", staticmethod(load_owl))
        graph = FOLIO(use_cache=False)
        if backend is None:
            assert graph._label_trie is None
            assert graph._lowercase_label_trie is None
        else:
            assert isinstance(graph._label_trie, backend.Trie)
            assert isinstance(graph._lowercase_label_trie, backend.Trie)
        return graph

    return load


@pytest.mark.parametrize("tagged_first", [True, False])
def test_language_tagged_alternative_label_casefold(load_graph, tagged_first):
    alternatives = [
        '<skos:altLabel xml:lang="de">Straße</skos:altLabel>',
        "<skos:altLabel>Straße</skos:altLabel>",
    ]
    if not tagged_first:
        alternatives.reverse()
    graph = load_graph(
        owl_document(f"""
        <owl:Class rdf:about="{ROAD_IRI}">
            <rdfs:label>Road</rdfs:label>
            {"".join(alternatives)}
        </owl:Class>
        """)
    )

    road = graph[ROAD_IRI]
    assert road.translations["de"] == "Straße"
    assert road.alternative_labels == ["Straße"]
    for _ in range(2):
        assert [cls.iri for cls in graph.search_by_prefix("STRASS")] == [ROAD_IRI]
        assert [
            cls.iri for cls in graph.search_by_prefix("Straß", case_sensitive=True)
        ] == [ROAD_IRI]
        assert graph.search_by_prefix("STRASS", case_sensitive=True) == []


@pytest.mark.parametrize("case_sensitive", [False, True])
def test_primary_label_precedence_and_deduplication(load_graph, case_sensitive):
    graph = load_graph(
        owl_document(f"""
        <owl:Class rdf:about="{ALTERNATIVE_IRI}">
            <rdfs:label>Other</rdfs:label>
            <skos:altLabel>Match</skos:altLabel>
        </owl:Class>
        <owl:Class rdf:about="{PRIMARY_IRI}">
            <rdfs:label>Match primary label</rdfs:label>
            <skos:altLabel>Match alias</skos:altLabel>
            <skos:altLabel>Match primary label</skos:altLabel>
        </owl:Class>
        """)
    )

    prefix = "Match" if case_sensitive else "MATCH"
    for _ in range(2):
        results = graph.search_by_prefix(prefix, case_sensitive=case_sensitive)
        assert [cls.iri for cls in results] == [PRIMARY_IRI, ALTERNATIVE_IRI]


def test_refresh_replaces_labels_and_invalidates_hits_and_misses(load_graph):
    documents = [
        owl_document(f"""
        <owl:Class rdf:about="{ROAD_IRI}">
            <rdfs:label>{primary}</rdfs:label>
            <skos:altLabel xml:lang="en">{alternative}</skos:altLabel>
        </owl:Class>
        """)
        for primary, alternative in [
            ("Before Primary", "Earlier Alias"),
            ("Future Primary", "Later Alias"),
        ]
    ]
    graph = load_graph(*documents)
    old_prefixes = ("Before", "Earlier")
    new_prefixes = ("Future", "Later")

    for case_sensitive in (False, True):
        for prefix in old_prefixes + new_prefixes:
            query = prefix if case_sensitive else prefix.upper()
            expected = [ROAD_IRI] if prefix in old_prefixes else []
            for _ in range(2):
                results = graph.search_by_prefix(query, case_sensitive=case_sensitive)
                assert [cls.iri for cls in results] == expected

    # Both cache paths must actually be warm before refresh can exercise invalidation.
    assert len(graph._prefix_cache) == 4
    assert len(graph._ci_prefix_cache) == 4
    graph.refresh()

    for case_sensitive in (False, True):
        for prefix in old_prefixes + new_prefixes:
            query = prefix if case_sensitive else prefix.upper()
            expected = [ROAD_IRI] if prefix in new_prefixes else []
            for _ in range(2):
                results = graph.search_by_prefix(query, case_sensitive=case_sensitive)
                assert [cls.iri for cls in results] == expected
    assert graph[ROAD_IRI].label == "Future Primary"
    assert graph[ROAD_IRI].alternative_labels == ["Later Alias"]
    assert graph[ROAD_IRI].translations["en"] == "Later Alias"
