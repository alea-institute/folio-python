"""kaos-nlp-core search backend: quality, GIL release, laziness and fallback."""

import asyncio
import json
import threading
import time
from pathlib import Path

import pytest

import folio.graph
import folio.kaos_search
from folio import FOLIO
from folio.kaos_search import (
    SEARCH_BACKEND_ENV,
    KaosSearchIndices,
    tokenize_trigrams,
    tokenize_words,
)

requires_kaos = pytest.mark.skipif(
    not folio.kaos_search.KAOS_AVAILABLE,
    reason="kaos-nlp-core not installed (requires Python >= 3.13)",
)

EVAL_SET = Path(__file__).parents[1] / "benchmarks" / "search_eval" / "queries.json"
BASE = "https://folio.openlegalstandard.org/"
CONTRACT = f"{BASE}Rcontract"
NEGLIGENCE = f"{BASE}Rnegligence"
LOCAL_ONTOLOGY = f"""
<owl:Class rdf:about="{CONTRACT}"><rdfs:label>Contract Law</rdfs:label>
  <skos:altLabel>Agreement Law</skos:altLabel>
  <skos:definition>Rules governing legally binding agreements.</skos:definition>
</owl:Class>
<owl:Class rdf:about="{NEGLIGENCE}"><rdfs:label>Negligence</rdfs:label>
  <skos:definition>Failure to exercise reasonable care causing harm.</skos:definition>
</owl:Class>
"""


@pytest.fixture(scope="module")
def real_graph():
    return FOLIO(llm=None)


@pytest.fixture
def kaos_backend(monkeypatch):
    monkeypatch.setenv(SEARCH_BACKEND_ENV, "auto")


def test_tokenizers():
    assert tokenize_words("Landlord-Tenant Law; U.S. children's") == [
        "landlord",
        "tenant",
        "law",
        "u",
        "s",
        "children",
        "s",
    ]
    assert tokenize_words(" ,. ") == []
    assert tokenize_trigrams("Trust") == ["#tr", "tru", "rus", "ust", "st#"]
    assert tokenize_trigrams("a") == ["#a#"]


def test_forced_fallback_disables_kaos(monkeypatch):
    monkeypatch.setenv(SEARCH_BACKEND_ENV, "rapidfuzz")
    assert not folio.kaos_search.kaos_enabled()


@requires_kaos
def test_local_label_and_definition_search(local_graph, kaos_backend):
    graph = local_graph(LOCAL_ONTOLOGY)
    results = graph.search_by_label("contract law")
    assert results[0][0].iri == CONTRACT
    assert results[0][1] == 100.0
    # typo tolerance comes from character trigrams
    assert graph.search_by_label("neglegence")[0][0].iri == NEGLIGENCE
    # alt labels are searched only when requested
    assert graph.search_by_label("agreement", limit=1)[0][0].iri == CONTRACT
    assert all(
        c.iri != CONTRACT
        for c, _ in graph.search_by_label("agreement", include_alt_labels=False)
    )
    definition = graph.search_by_definition("reasonable care harm")
    assert definition[0][0].iri == NEGLIGENCE
    assert 0 < definition[0][1] <= 100
    assert graph.search_by_label("") == []
    assert graph.search_by_definition("?!") == []


@requires_kaos
def test_kaos_path_does_not_need_rapidfuzz(local_graph, kaos_backend, monkeypatch):
    graph = local_graph(LOCAL_ONTOLOGY)
    monkeypatch.setattr(folio.graph, "rapidfuzz", None)
    assert graph.search_by_label("contract")[0][0].iri == CONTRACT
    assert graph.search_by_definition("binding agreements")[0][0].iri == CONTRACT


def test_forced_fallback_uses_rapidfuzz(local_graph, monkeypatch):
    monkeypatch.setenv(SEARCH_BACKEND_ENV, "rapidfuzz")
    graph = local_graph(LOCAL_ONTOLOGY)
    FOLIO._basic_search.cache_clear()
    label = graph.search_by_label("contract law")
    definition = graph.search_by_definition("reasonable care")
    assert FOLIO._basic_search.cache_info().misses == 2
    assert label[0][0].iri == CONTRACT
    assert definition and all(0 <= score <= 100 for _, score in definition)
    # no kaos index was built on the fallback path
    assert graph._kaos_indices._labels == {}
    assert graph._kaos_indices._definitions is None


@requires_kaos
def test_scores_are_sorted_and_bounded(real_graph, kaos_backend):
    for query in ("contract law", "copyrite", "xyzzy nonsense", "离婚"):
        scores = [score for _, score in real_graph.search_by_label(query)]
        assert scores == sorted(scores, reverse=True)
        assert all(0 <= score <= 100 for score in scores)
    scores = [s for _, s in real_graph.search_by_definition("dissolution of marriage")]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 100 for score in scores)


@requires_kaos
def test_indices_built_once_under_concurrency():
    builds = []
    barrier = threading.Barrier(8)

    def source():
        builds.append(1)
        time.sleep(0.05)
        return ["Contract Law", "Negligence"]

    indices = KaosSearchIndices()

    def worker():
        barrier.wait()
        indices.labels(True, source)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(builds) == 1
    indices.clear()
    indices.labels(True, source)
    assert len(builds) == 2


@requires_kaos
def test_refresh_rebuilds_from_new_ontology(local_graph, kaos_backend, monkeypatch):
    graph = local_graph(LOCAL_ONTOLOGY)
    assert graph.search_by_label("contract law")[0][1] == 100.0
    renamed = local_graph(LOCAL_ONTOLOGY.replace("Contract Law", "Tort Law"))
    # local_graph re-patched FOLIO.load_owl to serve the renamed ontology
    del renamed
    graph.refresh()
    assert graph._kaos_indices._labels == {}
    assert graph.search_by_label("tort law")[0][0].iri == CONTRACT
    assert graph.search_by_label("tort law")[0][1] == 100.0


@requires_kaos
def test_eval_set_quality(real_graph, kaos_backend):
    """The kaos backend must keep its measured quality on the labelled eval set."""
    data = json.loads(EVAL_SET.read_text(encoding="utf-8"))

    def hit_at_5(search, queries):
        hits = 0
        for item in queries:
            expected = {e["iri"] for e in item["expected"]}
            hits += any(c.iri in expected for c, _ in search(item["query"])[:5])
        return hits / len(queries)

    assert len(data["label_queries"]) >= 40
    assert len(data["definition_queries"]) >= 20
    assert hit_at_5(real_graph.search_by_label, data["label_queries"]) >= 0.95
    assert hit_at_5(real_graph.search_by_definition, data["definition_queries"]) >= 0.85


@requires_kaos
def test_kaos_search_does_not_block_event_loop(real_graph, kaos_backend):
    """Threaded kaos searches must leave an asyncio loop responsive (GIL released)."""
    data = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    label_queries = [q["query"] for q in data["label_queries"]][:20]
    definition_queries = [q["query"] for q in data["definition_queries"]][:20]
    # build both indices up front: the one-time build is not what is measured
    real_graph.search_by_label("warm up")
    real_graph.search_by_definition("warm up")

    async def run():
        worst = 0.0
        done = False

        async def ticker():
            nonlocal worst
            while not done:
                start = time.perf_counter()
                await asyncio.sleep(0.001)
                worst = max(worst, time.perf_counter() - start - 0.001)

        task = asyncio.create_task(ticker())
        await asyncio.sleep(0.01)
        jobs = [
            asyncio.to_thread(real_graph.search_by_label, q) for q in label_queries
        ] + [
            asyncio.to_thread(real_graph.search_by_definition, q)
            for q in definition_queries
        ]
        results = await asyncio.gather(*jobs)
        done = True
        await task
        return worst, results

    worst, results = asyncio.run(run())
    assert all(results)
    # RapidFuzz holds the GIL for the whole scan (~1-3 s worst stall here);
    # kaos releases it inside each query, leaving only Python glue.
    assert worst < 0.1, f"event loop stalled for {worst * 1000:.0f} ms"
