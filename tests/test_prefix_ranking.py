"""Offline ranking contracts, exercised through both optional prefix backends."""

import importlib

import pytest

import folio.graph
from folio.graph import FOLIO_TYPE_IRIS, FOLIOTypes, OWL_THING


BASE = "https://folio.openlegalstandard.org/"
LOCATED_IN = "http://www.w3.org/2000/01/rdf-schema#locatedIn"


def iri(name):
    return name if "://" in name else BASE + name


def concept(name, label=None, parents=(), extra=""):
    edges = "".join(
        f'<rdfs:subClassOf rdf:resource="{iri(parent)}"/>' for parent in parents
    )
    return (
        f'<owl:Class rdf:about="{iri(name)}">'
        f"<rdfs:label>{label or name}</rdfs:label>{edges}{extra}</owl:Class>"
    )


def restriction(target, predicate=LOCATED_IN):
    return (
        "<rdfs:subClassOf><owl:Restriction>"
        f'<owl:onProperty rdf:resource="{predicate}"/>'
        f'<owl:someValuesFrom rdf:resource="{iri(target)}"/>'
        "</owl:Restriction></rdfs:subClassOf>"
    )


def bonus(graph, name):
    return graph._prefix_rank_bonus[graph.iri_to_index[iri(name)]]


def test_minimum_depth_handles_missing_parents_and_cycles(local_graph):
    graph = local_graph(
        concept("root", parents=(OWL_THING,))
        + concept("custom-root")
        + concept("middle", parents=("root",))
        + concept("shortest", parents=("middle", "root", "missing"))
        + concept("connected-a", parents=("connected-b", "shortest"))
        + concept("connected-b", parents=("connected-a",))
        + concept("cycle-a", parents=("cycle-b",))
        + concept("cycle-b", parents=("cycle-a",))
        + concept("orphan", parents=("missing",))
    )
    for name, depth in {
        "root": 1,
        "custom-root": 1,
        "middle": 2,
        "shortest": 2,
        "connected-a": 3,
        "connected-b": 4,
    }.items():
        assert bonus(graph, name) == pytest.approx(5 / (1 + depth))
    for name in ("cycle-a", "cycle-b", "orphan"):
        assert bonus(graph, name) == 0
    assert len(graph._prefix_rank_bonus) == len(graph.classes)


@pytest.mark.parametrize(
    "branch,penalized",
    [
        (FOLIOTypes.LANGUAGE, True),
        (FOLIOTypes.LOCATION, True),
        (FOLIOTypes.STANDARDS_COMPATIBILITY, True),
        (FOLIOTypes.SYSTEM_IDENTIFIERS, True),
        (FOLIOTypes.MATTER_NARRATIVE, True),
        (FOLIOTypes.CURRENCY, True),
        (FOLIOTypes.DATA_FORMAT, True),
        (FOLIOTypes.MATTER_NARRATIVE_FORMAT, False),
        (FOLIOTypes.AREA_OF_LAW, False),
    ],
)
def test_branch_roots_descendants_and_mixed_membership(local_graph, branch, penalized):
    root = FOLIO_TYPE_IRIS[branch]
    ordinary = FOLIO_TYPE_IRIS[FOLIOTypes.SERVICE]
    graph = local_graph(
        concept(root)
        + concept(ordinary)
        + concept("descendant", parents=(root,))
        + concept("mixed", parents=(root, ordinary))
        + concept("unclassified")
    )
    penalty = 2 if penalized else 0
    assert bonus(graph, root) == pytest.approx(5 / 2 - penalty)
    assert bonus(graph, "descendant") == pytest.approx(5 / 3 - penalty)
    assert bonus(graph, "mixed") == pytest.approx(5 / 3)
    assert bonus(graph, "unclassified") == pytest.approx(5 / 2)


def test_location_references_count_only_distinct_valid_direct_sources(local_graph):
    location = FOLIO_TYPE_IRIS[FOLIOTypes.LOCATION]
    good = restriction("synthetic-place")
    # Invalid shapes must not inflate prominence, even for an existing target.
    malformed = [
        restriction("synthetic-place", predicate="https://example.org/wrong"),
        good.replace("owl:someValuesFrom", "owl:allValuesFrom"),
        good.replace("<owl:onProperty rdf:resource=", "<owl:onProperty wrong="),
        good.replace("<owl:Restriction>", "<owl:Class><owl:Restriction>").replace(
            "</owl:Restriction>", "</owl:Restriction></owl:Class>"
        ),
        good.replace("<owl:onProperty", "<owl:Class><owl:onProperty").replace(
            "<owl:someValuesFrom", "</owl:Class><owl:someValuesFrom"
        ),
        good.replace(
            "</owl:Restriction>",
            f'<owl:someValuesFrom rdf:resource="{iri("other")}"/></owl:Restriction>',
        ),
    ]
    graph = local_graph(
        concept(location)
        + concept("synthetic-place", parents=(location,), extra=good)
        + concept("unused-place", parents=(location,))
        + concept("ordinary")
        + concept("source-one", extra=good * 3)
        + concept("source-two", extra=good)
        + "".join(concept(f"invalid-{i}", extra=xml) for i, xml in enumerate(malformed))
        + concept("bad-targets", extra=restriction("absent") + restriction("ordinary"))
        + f'<owl:Class rdf:about="{iri("unlabelled")}">{good}</owl:Class>'
        + f"<owl:Class>{good}</owl:Class>"
    )
    assert bonus(graph, "synthetic-place") == pytest.approx(5 / 3 - 2 + 5 * 2 / 3)
    assert bonus(graph, "unused-place") == pytest.approx(5 / 3 - 2)
    assert bonus(graph, "ordinary") == pytest.approx(5 / 2)


def test_ranking_metadata_does_not_change_public_parser_contents(local_graph):
    graph = local_graph(
        concept("root")
        + concept("child", parents=("root",), extra=restriction("root"))
        + f'<owl:ObjectProperty rdf:about="{iri("property")}">'
        "<rdfs:label>Property</rdfs:label></owl:ObjectProperty>"
    )
    before = (
        [item.model_dump() for item in graph.classes],
        [item.model_dump() for item in graph.object_properties],
        list(graph.triples),
    )
    assert len(graph.classes) == 2
    assert len(graph.object_properties) == 1
    graph._build_prefix_rank_bonus()
    assert before == (
        [item.model_dump() for item in graph.classes],
        [item.model_dump() for item in graph.object_properties],
        graph.triples,
    )


@pytest.fixture(params=["marisa", "python"])
def prefix_backend(request, monkeypatch):
    backend = (
        importlib.import_module("marisa_trie") if request.param == "marisa" else None
    )
    monkeypatch.setattr(folio.graph, "marisa_trie", backend)
    return backend


@pytest.fixture
def ranked_graph(local_graph, prefix_backend):
    def load(contents):
        graph = local_graph(contents)
        if prefix_backend is None:
            assert graph._label_trie is None
            assert graph._lowercase_label_trie is None
        else:
            assert isinstance(graph._label_trie, prefix_backend.Trie)
            assert isinstance(graph._lowercase_label_trie, prefix_backend.Trie)
        return graph

    return load


@pytest.fixture(params=[True, False])
def case_sensitive(request):
    return request.param


def results(graph, prefix, case_sensitive):
    return [item.iri for item in graph.search_by_prefix(prefix, case_sensitive)]


def test_california_and_tax_examples(ranked_graph, case_sensitive):
    location = FOLIO_TYPE_IRIS[FOLIOTypes.LOCATION]
    law = FOLIO_TYPE_IRIS[FOLIOTypes.AREA_OF_LAW]
    graph = ranked_graph(
        concept(location)
        + concept("continent", parents=(location,))
        + concept("country", parents=("continent",))
        + concept("caldas", "Caldas", parents=("country",))
        + concept("california", "California", parents=("country",))
        + "".join(
            concept(f"court-{i}", extra=restriction("california")) for i in range(8)
        )
        + concept(law)
        + concept("tax-revenue", "Tax and Revenue Law", parents=(law,))
        + concept("tax-law", "Tax Law", parents=("tax-revenue",))
        + concept("tax-credit", "Tax Credit", parents=("tax-law",))
    )
    for _ in range(2):
        for prefix in ["Cal"] if case_sensitive else ["Cal", "cal", "cAL"]:
            assert results(graph, prefix, case_sensitive) == [
                iri("california"),
                iri("caldas"),
            ]
        for prefix in ["Tax"] if case_sensitive else ["Tax", "tax", "tAX"]:
            assert results(graph, prefix, case_sensitive)[0] == iri("tax-law")


@pytest.mark.parametrize(
    "contents,prefix,expected",
    [
        (
            concept("extension", "Match extension") + concept("exact", "Match"),
            "Match",
            ["exact", "extension"],
        ),
        (
            concept("long", "Matching long") + concept("short", "Match short"),
            "Mat",
            ["short", "long"],
        ),
        (
            concept("root")
            + concept("a-deep", "Match", parents=("root",))
            + concept("z-shallow", "Match"),
            "Mat",
            ["z-shallow", "a-deep"],
        ),
        (
            concept(FOLIO_TYPE_IRIS[FOLIOTypes.LOCATION])
            + concept(FOLIO_TYPE_IRIS[FOLIOTypes.AREA_OF_LAW])
            + concept(
                "a-location", "Match", parents=(FOLIO_TYPE_IRIS[FOLIOTypes.LOCATION],)
            )
            + concept(
                "z-law", "Match", parents=(FOLIO_TYPE_IRIS[FOLIOTypes.AREA_OF_LAW],)
            ),
            "Mat",
            ["z-law", "a-location"],
        ),
        (
            concept("z-primary", "Match")
            + concept("a-alias", "Other", extra="<skos:altLabel>Match</skos:altLabel>")
            + concept("y-primary", "Match extension"),
            "Match",
            ["z-primary", "y-primary", "a-alias"],
        ),
        (
            concept(
                "z-best",
                "Match extension",
                extra="<skos:altLabel>Match</skos:altLabel>",
            )
            + concept("a-exact", "Match")
            + concept(
                "b-alias", "Other", extra="<skos:altLabel>Match</skos:altLabel>" * 2
            ),
            "Match",
            ["a-exact", "z-best", "b-alias"],
        ),
    ],
    ids=["exact", "length", "depth", "branch", "provenance", "best-occurrence"],
)
def test_individual_signals_and_best_occurrence(
    ranked_graph, case_sensitive, contents, prefix, expected
):
    graph = ranked_graph(contents)
    assert results(graph, prefix, case_sensitive) == [iri(name) for name in expected]


def test_primary_and_exact_dominate_secondary_scores(ranked_graph, case_sensitive):
    location = FOLIO_TYPE_IRIS[FOLIOTypes.LOCATION]
    graph = ranked_graph(
        concept(location)
        + concept("deep", parents=(location,))
        + concept("primary", "Match" + "x" * 1000, parents=("deep",))
        + concept("alias", "Other", extra="<skos:altLabel>Match</skos:altLabel>")
        + concept("exact", "Exact", parents=("deep",))
        + concept("extension", "Exact extension", parents=(location,))
        + "".join(
            concept(f"court-{i}", extra=restriction("extension")) for i in range(100)
        )
    )
    assert results(graph, "Match", case_sensitive) == [iri("primary"), iri("alias")]
    assert results(graph, "Exact", case_sensitive) == [iri("exact"), iri("extension")]
    assert bonus(graph, "extension") == pytest.approx(5 / 3 - 2 + 500 / 101)
    assert bonus(graph, "extension") < 5 / 3 - 2 + 5


def test_unicode_casefold_collisions_and_deterministic_ties(ranked_graph):
    # Reversed input order and differing original lengths must not decide folded ties.
    graph = ranked_graph(
        concept("z-road", "Straße")
        + concept("a-road", "STRASSE")
        + concept("b-road", "Other", extra="<skos:altLabel>strasse</skos:altLabel>")
    )
    assert results(graph, "STRASSE", False) == [
        iri("a-road"),
        iri("z-road"),
        iri("b-road"),
    ]
    assert results(graph, "Stra", True) == [iri("z-road")]
    assert results(graph, "STR", True) == [iri("a-road")]


def test_ties_ignore_candidate_order_and_short_labels_keep_backend_membership(
    ranked_graph, prefix_backend, case_sensitive
):
    graph = ranked_graph(
        concept("z-tie", "Match") + concept("a-tie", "Match") + concept("short", "Ma")
    )
    expected = [iri("a-tie"), iri("z-tie")]
    if prefix_backend is None:
        expected.insert(0, iri("short"))
    assert results(graph, "Ma", case_sensitive) == expected
    assert results(graph, "", case_sensitive) == expected
    assert results(graph, "Absent", case_sensitive) == []


def test_caches_remain_bounded_and_hits_do_not_score_or_rebuild(
    ranked_graph, monkeypatch
):
    graph = ranked_graph(
        "".join(concept(f"match-{i}", f"Match-{i}") for i in range(140))
    )
    metadata = graph._prefix_rank_bonus
    for case_sensitive in (False, True):
        for i in range(140):
            for prefix in (f"Match-{i}", f"Absent-{i}"):
                graph.search_by_prefix(prefix, case_sensitive)
        cache = graph._prefix_cache if case_sensitive else graph._ci_prefix_cache
        assert len(cache) == 128
        assert next(iter(cache)) == ("Match-76" if case_sensitive else "match-76")
        assert cache["Absent-139" if case_sensitive else "absent-139"] == []
    assert graph._prefix_rank_bonus is metadata
    assert graph._basic_search.cache_parameters()["maxsize"] == 128

    def unexpected(*args, **kwargs):
        pytest.fail("Cache hits must not score or rebuild ranking metadata")

    monkeypatch.setattr(graph, "_rank_prefix_matches", unexpected)
    monkeypatch.setattr(graph, "_build_prefix_rank_bonus", unexpected)
    for prefix, case_sensitive in [("Match-139", True), ("mAtCh-139", False)]:
        assert results(graph, prefix, case_sensitive) == [iri("match-139")]
    assert graph.search_by_prefix("ABSENT-139") == []
    assert len(graph._ci_prefix_cache) == 128


def test_refresh_replaces_structural_ranking_and_cached_misses(ranked_graph):
    location = FOLIO_TYPE_IRIS[FOLIOTypes.LOCATION]
    law = FOLIO_TYPE_IRIS[FOLIOTypes.AREA_OF_LAW]

    def contents(preferred):
        other = "b" if preferred == "a" else "a"
        return (
            concept(location)
            + concept(law)
            + concept("deep", parents=(location,))
            + concept(preferred, "Match", parents=(law,))
            + concept(other, "Match", parents=("deep",))
            + concept("place-a", "Place", parents=(location,))
            + concept("place-b", "Place", parents=(location,))
            + concept("source", extra=restriction(f"place-{preferred}"))
        )

    graph = ranked_graph(contents("a"))
    for mode in (False, True):
        assert results(graph, "Match", mode) == [iri("a"), iri("b")]
        assert results(graph, "Place", mode) == [iri("place-a"), iri("place-b")]
        assert results(graph, "New", mode) == []
    old_metadata = list(graph._prefix_rank_bonus)
    # The fixture replaces the loader with the next document, as refresh would fetch it.
    ranked_graph(contents("b") + concept("new", "New"))
    graph.refresh()
    assert graph._prefix_rank_bonus != old_metadata
    assert len(graph._prefix_rank_bonus) == len(graph.classes) == 9
    for mode in (False, True):
        assert results(graph, "Match", mode) == [iri("b"), iri("a")]
        assert results(graph, "Place", mode) == [iri("place-b"), iri("place-a")]
        assert results(graph, "New", mode) == [iri("new")]


def test_first_metadata_build_preserves_public_parse_results(local_graph, monkeypatch):
    original = folio.graph.FOLIO._build_prefix_rank_bonus
    snapshots = []

    def capture_build(graph):
        before = (
            [item.model_dump() for item in graph.classes],
            [item.model_dump() for item in graph.object_properties],
            list(graph.triples),
        )
        original(graph)
        assert before == (
            [item.model_dump() for item in graph.classes],
            [item.model_dump() for item in graph.object_properties],
            graph.triples,
        )
        snapshots.append(before)

    monkeypatch.setattr(folio.graph.FOLIO, "_build_prefix_rank_bonus", capture_build)
    graph = local_graph(
        concept("root")
        + concept("child", parents=("root",), extra=restriction("root"))
        + f'<owl:ObjectProperty rdf:about="{iri("property")}">'
        "<rdfs:label>Property</rdfs:label></owl:ObjectProperty>"
    )
    assert len(snapshots) == 1
    assert len(graph.classes) == 2
    assert len(graph.object_properties) == 1
