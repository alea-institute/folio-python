"""Executable README recipes against a synthetic ontology, without downloads."""

import importlib.util
from pathlib import Path

import pytest

import folio.graph
from folio import FOLIO, FOLIOTypes, FOLIO_TYPE_IRIS


BASE = "https://folio.openlegalstandard.org/"
LAW = FOLIO_TYPE_IRIS[FOLIOTypes.AREA_OF_LAW]
ACTOR = FOLIO_TYPE_IRIS[FOLIOTypes.ACTOR_PLAYER]
RECIPE_PATH = Path(__file__).resolve().parents[1] / "examples/structured_queries.py"


def load_recipes():
    # Examples are repository sources, excluded from the installed distribution.
    spec = importlib.util.spec_from_file_location("structured_queries", RECIPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def recipes():
    return load_recipes()


@pytest.fixture
def graph(monkeypatch):
    monkeypatch.setattr(folio.graph, "alea_llm_client", None)
    monkeypatch.setattr(folio.graph, "marisa_trie", None)
    monkeypatch.setattr(folio.graph, "rapidfuzz", None)
    document = f"""<rdf:RDF
        xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
        xmlns:owl="http://www.w3.org/2002/07/owl#"
        xmlns:skos="http://www.w3.org/2004/02/skos/core#">
        <owl:Class rdf:about="{BASE}{LAW}">
            <rdfs:label>Area of Law</rdfs:label>
            <skos:definition>Includes trust law.</skos:definition>
        </owl:Class>
        <owl:Class rdf:about="{BASE}{ACTOR}">
            <rdfs:label>Actor / Player</rdfs:label>
        </owl:Class>
        <owl:Class rdf:about="{BASE}Rtrust">
            <rdfs:label>Trust Law</rdfs:label>
            <rdfs:subClassOf rdf:resource="{BASE}{LAW}"/>
        </owl:Class>
        <owl:Class rdf:about="{BASE}Restate">
            <rdfs:label>Estate Planning</rdfs:label>
            <skos:definition>Planning with a trust.</skos:definition>
            <rdfs:subClassOf rdf:resource="{BASE}Rtrust"/>
        </owl:Class>
        <owl:Class rdf:about="{BASE}Rcontract">
            <rdfs:label>Contract Law</rdfs:label>
            <rdfs:subClassOf rdf:resource="{BASE}{LAW}"/>
        </owl:Class>
        <owl:Class rdf:about="{BASE}Routside">
            <rdfs:label>Trust Organization</rdfs:label>
            <rdfs:subClassOf rdf:resource="{BASE}{ACTOR}"/>
        </owl:Class>
        <owl:Class rdf:about="{BASE}Rtrustee">
            <rdfs:label>Trustee</rdfs:label>
            <rdfs:subClassOf rdf:resource="{BASE}{ACTOR}"/>
        </owl:Class>
        <owl:Class rdf:about="{BASE}RcoTrustee">
            <rdfs:label>Co-Trustee</rdfs:label>
            <rdfs:subClassOf rdf:resource="{BASE}{ACTOR}"/>
        </owl:Class>
        <owl:ObjectProperty rdf:about="{BASE}PhasTrustee">
            <rdfs:label>has trustee</rdfs:label>
            <rdfs:domain rdf:resource="{BASE}Rtrust"/>
            <rdfs:domain rdf:resource="{BASE}Restate"/>
            <rdfs:range rdf:resource="{BASE}Rtrustee"/>
            <rdfs:range rdf:resource="{BASE}RcoTrustee"/>
            <owl:inverseOf rdf:resource="{BASE}PtrusteeOf"/>
        </owl:ObjectProperty>
        <owl:ObjectProperty rdf:about="{BASE}Psecondary">
            <rdfs:label>has secondary trustee</rdfs:label>
            <rdfs:domain rdf:resource="{BASE}Rtrust"/>
            <rdfs:domain rdf:resource="{BASE}Restate"/>
            <rdfs:range rdf:resource="{BASE}Rtrustee"/>
            <rdfs:range rdf:resource="{BASE}RcoTrustee"/>
        </owl:ObjectProperty>
        <owl:ObjectProperty rdf:about="{BASE}PnoInverse">
            <rdfs:label>has trustee</rdfs:label>
            <rdfs:domain rdf:resource="{BASE}Rtrust"/>
            <rdfs:range rdf:resource="{BASE}Rtrustee"/>
        </owl:ObjectProperty>
        <owl:ObjectProperty rdf:about="{BASE}PwrongDomain">
            <rdfs:label>has trustee</rdfs:label>
            <rdfs:domain rdf:resource="{BASE}Routside"/>
            <rdfs:range rdf:resource="{BASE}Rtrustee"/>
            <owl:inverseOf rdf:resource="{BASE}PtrusteeOf"/>
        </owl:ObjectProperty>
        <owl:ObjectProperty rdf:about="{BASE}PwrongRange">
            <rdfs:label>has trustee</rdfs:label>
            <rdfs:domain rdf:resource="{BASE}Rtrust"/>
            <rdfs:range rdf:resource="{BASE}Routside"/>
            <owl:inverseOf rdf:resource="{BASE}PtrusteeOf"/>
        </owl:ObjectProperty>
        <owl:ObjectProperty rdf:about="{BASE}PwrongText">
            <rdfs:label>refers to</rdfs:label>
            <rdfs:domain rdf:resource="{BASE}Rtrust"/>
            <rdfs:range rdf:resource="{BASE}Rtrustee"/>
            <owl:inverseOf rdf:resource="{BASE}PreferredBy"/>
        </owl:ObjectProperty>
        <owl:ObjectProperty rdf:about="{BASE}Pancestor">
            <rdfs:label>has trustee</rdfs:label>
            <rdfs:domain rdf:resource="{BASE}{LAW}"/>
            <rdfs:range rdf:resource="{BASE}{ACTOR}"/>
            <owl:inverseOf rdf:resource="{BASE}PtrusteeOf"/>
        </owl:ObjectProperty>
    </rdf:RDF>"""
    monkeypatch.setattr(FOLIO, "load_owl", staticmethod(lambda **kwargs: document))
    return FOLIO(use_cache=False)


def iris(items):
    return {item.iri for item in items}


def associations(rows):
    return {(source.iri, prop.iri, target.iri) for source, prop, target in rows}


EXPECTED_ASSOCIATIONS = {
    (BASE + source, BASE + prop, BASE + target)
    for source in ("Rtrust", "Restate")
    for prop in ("PhasTrustee", "Psecondary")
    for target in ("Rtrustee", "RcoTrustee")
} | {(BASE + "Rtrust", BASE + "PnoInverse", BASE + "Rtrustee")}


def test_recipe_import_does_not_construct_graph(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("Importing recipes must not construct a graph")

    monkeypatch.setattr(FOLIO, "__init__", fail)
    load_recipes()


@pytest.mark.parametrize("branch", ["AREA_OF_LAW", "area of law"])
def test_classes_in_branch(graph, recipes, branch):
    results = recipes.classes_in_branch(graph, text="TRUST", branch=branch)
    assert iris(results) == {BASE + "Rtrust", BASE + "Restate"}
    assert len(results) == 2


@pytest.mark.parametrize(
    "text,branch",
    [("missing", "AREA_OF_LAW"), ("trust", "unknown"), ("trustee", "AREA_OF_LAW")],
)
def test_class_filters_empty_intersection(graph, recipes, text, branch):
    # Both filters in the trustee/Area of Law case have matches in isolation.
    assert graph.query(any_text="trustee")
    assert graph.query(branch="AREA_OF_LAW")
    assert recipes.classes_in_branch(graph, text=text, branch=branch) == []


def test_properties_between(graph, recipes):
    results = recipes.properties_between(
        graph,
        text="HAS",
        domain_iri="Rtrust",
        range_iri=BASE + "Rtrustee",
        has_inverse=True,
    )
    assert iris(results) == {BASE + "PhasTrustee"}
    assert len(results) == 1


def test_property_endpoints_are_explicit(graph, recipes):
    assert iris(
        recipes.properties_between(
            graph,
            text="has",
            domain_iri=LAW,
            range_iri=ACTOR,
        )
    ) == {BASE + "Pancestor"}
    assert (
        recipes.properties_between(
            graph,
            text="has",
            domain_iri="Restate",
            range_iri=ACTOR,
        )
        == []
    )
    assert (
        recipes.properties_between(
            graph,
            text="has",
            domain_iri=LAW,
            range_iri="Rtrustee",
        )
        == []
    )


def test_property_filters_empty_intersection(graph, recipes):
    assert graph.query_properties(label="refers")
    assert graph.query_properties(domain_iri="Restate", range_iri="Rtrustee")
    assert (
        recipes.properties_between(
            graph,
            text="refers",
            domain_iri="Restate",
            range_iri="Rtrustee",
        )
        == []
    )


def test_connections_between_branches(graph, recipes):
    rows = recipes.connections_between_branches(
        graph,
        source_text="trust",
        source_branch="AREA_OF_LAW",
        target_text="trustee",
        target_branch="ACTOR_PLAYER",
        property_text="has",
    )
    assert associations(rows) == EXPECTED_ASSOCIATIONS
    assert len(rows) == 9


@pytest.mark.parametrize(
    "overrides",
    [
        {"source_text": "missing"},
        {"target_text": "missing"},
        {"source_branch": "unknown"},
        {"property_text": "missing"},
    ],
)
def test_composition_empty_results(graph, recipes, overrides):
    options = dict(
        source_text="trust",
        source_branch="AREA_OF_LAW",
        target_text="trustee",
        target_branch="ACTOR_PLAYER",
        property_text="has",
    )
    options.update(overrides)
    assert recipes.connections_between_branches(graph, **options) == []


@pytest.mark.parametrize(
    "source_limit,target_limit,property_limit,expected_count",
    [
        (1, 2, 1, 2),
        (2, 1, 1, 2),
        (2, 2, 1, 4),
        (2, 2, 2, 8),
    ],
)
def test_composition_limits(
    graph, recipes, source_limit, target_limit, property_limit, expected_count
):
    rows = recipes.connections_between_branches(
        graph,
        source_text="trust",
        source_branch="AREA_OF_LAW",
        target_text="trustee",
        target_branch="ACTOR_PLAYER",
        property_text="has",
        source_limit=source_limit,
        target_limit=target_limit,
        property_limit_per_pair=property_limit,
    )
    assert len(rows) == expected_count
    assert len(associations(rows)) == expected_count
    assert associations(rows) <= EXPECTED_ASSOCIATIONS
    assert len({source.iri for source, _, _ in rows}) == source_limit
    assert len({target.iri for _, _, target in rows}) == target_limit
    for source in {source.iri for source, _, _ in rows}:
        for target in {target.iri for _, _, target in rows}:
            assert (
                sum(s.iri == source and t.iri == target for s, _, t in rows)
                == property_limit
            )


def test_readme_text_and_branch(graph):
    results = graph.query(any_text="trust", branch="AREA_OF_LAW")
    assert iris(results) == {BASE + "Rtrust", BASE + "Restate"}


def test_readme_regex_labels(graph):
    results = graph.query(label="^Contract", match_mode="regex", limit=5)
    assert iris(results) == {BASE + "Rcontract"}


def test_readme_leaf_descendants(graph):
    results = graph.query(
        parent_iri="RSYBzf149Mi5KE0YtmpUmr", has_children=False, limit=10
    )
    assert iris(results) == {BASE + "Restate", BASE + "Rcontract"}


def test_readme_inverse_properties(graph):
    results = graph.query_properties(has_inverse=True)
    assert iris(results) == {
        BASE + name
        for name in (
            "PhasTrustee",
            "PwrongDomain",
            "PwrongRange",
            "PwrongText",
            "Pancestor",
        )
    }
