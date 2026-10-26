"""Offline cache contracts and opt-in sustained measurements (see docs/benchmarks)."""

from collections import deque
from dataclasses import asdict, dataclass
import gc
import json
import time
import tracemalloc

import pytest

import folio.graph
from folio import FOLIO


CAPACITY = 128
CLASS_COUNT = 260
SCENARIOS = ("prefix-sensitive", "prefix-insensitive", "fuzzy-mixed")


def iri(index):
    return f"https://example.org/cache/{index:04d}"


def ontology_xml():
    classes = [
        f'''<owl:Class rdf:about="{iri(index)}">
          <rdfs:label>Case{index:04d}</rdfs:label>
          <skos:altLabel>Alias{index:04d}</skos:altLabel>
          <skos:altLabel>Case{index:04d} alternate</skos:altLabel>
          <skos:definition>Meaning{index:04d}</skos:definition>
        </owl:Class>'''
        for index in range(CLASS_COUNT)
    ]
    for index, label, alt in (
        (260, "Order", "Order duplicate"),
        (261, "Order longer", "Other"),
        (262, "Unrelated", "Order alias"),
    ):
        classes.append(f'''<owl:Class rdf:about="{iri(index)}">
          <rdfs:label>{label}</rdfs:label><skos:altLabel>{alt}</skos:altLabel>
          <skos:definition>Meaning{index:04d}</skos:definition>
        </owl:Class>''')
    return (
        """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
        xmlns:owl="http://www.w3.org/2002/07/owl#"
        xmlns:skos="http://www.w3.org/2004/02/skos/core#">"""
        + "".join(classes)
        + "</rdf:RDF>"
    )


@pytest.fixture
def graph_factory(monkeypatch):
    """Construct normally, replacing only external data/provider boundaries."""
    xml = ontology_xml()
    monkeypatch.setattr(FOLIO, "load_owl", staticmethod(lambda **kwargs: xml))
    monkeypatch.setattr(folio.graph, "alea_llm_client", None)
    FOLIO._basic_search.cache_clear()
    try:
        yield lambda: FOLIO(use_cache=False)
    finally:
        FOLIO._basic_search.cache_clear()


@pytest.fixture
def offline_graph(graph_factory):
    return graph_factory()


@pytest.mark.parametrize("sensitive", [True, False])
def test_prefix_capacity_fifo_and_positive_recomputation(offline_graph, sensitive):
    graph = offline_graph
    cache = graph._prefix_cache if sensitive else graph._ci_prefix_cache

    def key(index):
        return f"Case{index:04d}" if sensitive else f"case{index:04d}"

    for index in range(CAPACITY):
        assert [c.iri for c in graph.search_by_prefix(key(index), sensitive)] == [
            iri(index)
        ]
        assert len(cache) == index + 1
    # Reads do not promote the oldest prefix entry: these are FIFO caches.
    graph.search_by_prefix(key(0), sensitive)
    graph.search_by_prefix(key(CAPACITY), sensitive)
    assert key(0) not in cache
    assert key(1) in cache
    for index in range(CAPACITY + 1, CLASS_COUNT):
        graph.search_by_prefix(key(index), sensitive)
        assert len(cache) == CAPACITY
    assert [c.iri for c in graph.search_by_prefix(key(0), sensitive)] == [iri(0)]
    before = list(cache)
    graph.search_by_prefix(key(0), sensitive)
    assert list(cache) == before


def test_casefold_reuses_cache(offline_graph):
    result = offline_graph.search_by_prefix("CASE0001")
    assert [c.iri for c in result] == [iri(1)]
    assert offline_graph.search_by_prefix("case0001") is result
    assert list(offline_graph._ci_prefix_cache) == ["case0001"]


@pytest.mark.parametrize("sensitive", [True, False])
def test_prefix_backend_order_and_deduplication(offline_graph, monkeypatch, sensitive):
    assert folio.graph.marisa_trie is not None
    query = "Order" if sensitive else "oRDER"
    assert [c.iri for c in offline_graph.search_by_prefix(query, sensitive)] == [
        iri(260),
        iri(261),
        iri(262),
    ]
    offline_graph._prefix_cache.clear()
    offline_graph._ci_prefix_cache.clear()
    monkeypatch.setattr(folio.graph, "marisa_trie", None)
    assert [c.iri for c in offline_graph.search_by_prefix(query, sensitive)] == [
        iri(260),
        iri(261),
        iri(262),
    ]


def fuzzy_call(graph, index, definition=False):
    if definition:
        return graph.search_by_definition(f"Meaning{index:04d}", limit=1)
    return graph.search_by_label(f"Alias{index:04d}", limit=1)


def test_public_fuzzy_capacity_lru_and_shared_corpus(offline_graph):
    graph = offline_graph
    for index in range(CAPACITY):
        result = fuzzy_call(graph, index)
        assert [(c.iri, score) for c, score in result] == [(iri(index), 100)]
        assert FOLIO._basic_search.cache_info().currsize == index + 1
    assert FOLIO._basic_search.cache_info().maxsize == CAPACITY
    fuzzy_call(graph, 0)  # LRU promotes this entry; the next label is evicted.
    info = FOLIO._basic_search.cache_info()
    assert info.hits == 1 and info.misses == CAPACITY
    assert [(c.iri, score) for c, score in fuzzy_call(graph, 0, True)] == [
        (iri(0), 100)
    ]
    assert FOLIO._basic_search.cache_info().currsize == CAPACITY
    fuzzy_call(graph, 0)
    assert FOLIO._basic_search.cache_info().hits == 2
    fuzzy_call(graph, 1)
    assert FOLIO._basic_search.cache_info().misses == CAPACITY + 2
    for index in range(CLASS_COUNT):
        fuzzy_call(graph, index, True)
        assert FOLIO._basic_search.cache_info().currsize == CAPACITY
    assert [(c.iri, score) for c, score in fuzzy_call(graph, 0)] == [(iri(0), 100)]


def test_factory_is_offline_and_restores_patches(graph_factory):
    graph = graph_factory()
    assert len(graph.classes) == 263
    assert graph.llm is None
    assert graph._label_trie is not None
    assert all(c.definition for c in graph.classes)


@dataclass(frozen=True)
class Budget:
    min_seconds: float = 60.0
    min_misses: int = 12_800
    min_checkpoints: int = 10
    deadline_seconds: float = 180.0
    checkpoint_seconds: float = 5.0
    batch_requests: int = 64


def cache_sizes(graph):
    return {
        "prefix_sensitive": len(graph._prefix_cache),
        "prefix_insensitive": len(graph._ci_prefix_cache),
        "fuzzy_shared": FOLIO._basic_search.cache_info().currsize,
    }


def perform_request(graph, scenario, index):
    """Return an observed miss, checking a known positive result every time."""
    if scenario == "fuzzy-mixed":
        before = FOLIO._basic_search.cache_info()
        result = fuzzy_call(graph, index, definition=bool(index % 2))
        assert [(c.iri, score) for c, score in result] == [(iri(index), 100)]
        after = FOLIO._basic_search.cache_info()
        assert (after.hits - before.hits) + (after.misses - before.misses) == 1
        return after.misses - before.misses
    sensitive = scenario == "prefix-sensitive"
    query = f"Case{index:04d}" if sensitive else f"cASE{index:04d}"
    cache = graph._prefix_cache if sensitive else graph._ci_prefix_cache
    key = query if sensitive else query.casefold()
    missed = key not in cache
    assert [c.iri for c in graph.search_by_prefix(query, sensitive)] == [iri(index)]
    return int(missed)


def request_index(sequence):
    # Two cold requests, then the same hot request twice. The cold cycle has
    # 256 keys; the four hot keys include both public fuzzy search methods.
    group, slot = divmod(sequence, 4)
    return 4 + (group * 2 + slot) % 256 if slot < 2 else group % 4


def timing_summary(samples):
    return {
        "batches": len(samples),
        "min_seconds": min(samples),
        "mean_seconds": sum(samples) / len(samples),
        "max_seconds": max(samples),
    }


class InsufficientPressure(AssertionError):
    pass


def measure_pressure(
    factory,
    scenario,
    budget=Budget(),
    *,
    clock=time.perf_counter,
    request=perform_request,
):
    """One continuous interval; all retained collections have a fixed bound."""
    if tracemalloc.is_tracing():
        raise RuntimeError("cache pressure requires ownership of tracemalloc")
    FOLIO._basic_search.cache_clear()
    tracemalloc.start()
    requests = misses = checkpoints = 0
    elapsed = 0.0
    try:
        graph = factory()
        assert folio.graph.marisa_trie is not None
        assert FOLIO._basic_search.cache_info().maxsize == CAPACITY
        # Warm public paths and fill the selected cache before the baseline.
        for index in range(CAPACITY):
            perform_request(graph, scenario, index)
        assert max(cache_sizes(graph).values()) == CAPACITY
        early = []
        late = deque(maxlen=8)
        samples = deque(maxlen=16)
        gc.collect()
        baseline_bytes = tracemalloc.get_traced_memory()[0]
        tracemalloc.reset_peak()
        start = clock()
        next_checkpoint = budget.checkpoint_seconds
        while True:
            batch_start = clock()
            for _ in range(budget.batch_requests):
                misses += request(graph, scenario, request_index(requests))
                requests += 1
            batch_seconds = clock() - batch_start
            if len(early) < 8:
                early.append(batch_seconds)
            late.append(batch_seconds)
            sizes = cache_sizes(graph)
            assert all(size <= CAPACITY for size in sizes.values())
            elapsed = clock() - start
            if elapsed >= next_checkpoint:
                # Each request's result died before GC; collection is excluded
                # from batch timings and is identical to baseline collection.
                gc.collect()
                current, peak = tracemalloc.get_traced_memory()
                elapsed = clock() - start
                checkpoints += 1
                samples.append(
                    {
                        "elapsed_seconds": elapsed,
                        "current_bytes": current,
                        "peak_bytes": peak,
                        "cache_entries": sizes,
                    }
                )
                next_checkpoint = elapsed + budget.checkpoint_seconds
            # Deadline wins even if this batch also crosses the success bar.
            if elapsed >= budget.deadline_seconds:
                raise InsufficientPressure("cooperative deadline reached")
            if (
                elapsed >= budget.min_seconds
                and misses >= budget.min_misses
                and checkpoints >= budget.min_checkpoints
            ):
                break
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        elapsed = clock() - start
        if elapsed >= budget.deadline_seconds:
            raise InsufficientPressure("deadline reached during final sample")
        return {
            "scenario": scenario,
            "backend": "rapidfuzz" if scenario == "fuzzy-mixed" else "marisa-trie",
            "outcome": "complete",
            "dataset": {
                "classes": 263,
                "traffic_classes": CLASS_COUNT,
                "cold_keys": 256,
                "hot_keys": 4,
            },
            "capacity_entries": CAPACITY,
            "criteria": asdict(budget),
            "elapsed_seconds": elapsed,
            "requests": requests,
            "misses": misses,
            "hits": requests - misses,
            "result_bearing_requests": requests,
            "capacity_turnovers": misses / CAPACITY,
            "checkpoint_count": checkpoints,
            "checkpoints": list(samples),
            "cache_entries": cache_sizes(graph),
            "batch_timing": {
                "early": timing_summary(early),
                "late": timing_summary(late),
            },
            "traced_memory": {
                "baseline_bytes": baseline_bytes,
                "final_bytes": current,
                "delta_bytes": current - baseline_bytes,
                "peak_bytes": peak,
            },
        }
    except Exception as exc:
        raise InsufficientPressure(
            f"{scenario}: elapsed_seconds={elapsed:.3f}, misses={misses}, "
            f"checkpoints={checkpoints}: {exc}"
        ) from exc
    finally:
        FOLIO._basic_search.cache_clear()
        tracemalloc.stop()


class TickClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        self.now += 0.01
        return self.now


def short_budget(**overrides):
    return Budget(
        **(
            {
                "min_seconds": 0.05,
                "min_misses": 16,
                "min_checkpoints": 2,
                "deadline_seconds": 2,
                "checkpoint_seconds": 0.01,
                "batch_requests": 16,
            }
            | overrides
        )
    )


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_runner_completes_only_with_measured_pressure(graph_factory, scenario):
    report = measure_pressure(
        graph_factory, scenario, short_budget(), clock=TickClock()
    )
    assert report["outcome"] == "complete"
    assert report["misses"] >= 16 and report["hits"] > 0
    assert report["elapsed_seconds"] >= 0.05 and report["checkpoint_count"] >= 2
    assert report["requests"] == report["misses"] + report["hits"]
    assert report["result_bearing_requests"] == report["requests"]
    assert FOLIO._basic_search.cache_info().currsize == 0
    assert not tracemalloc.is_tracing()


@pytest.mark.parametrize(
    "overrides,hit_only",
    [
        ({"deadline_seconds": 0.04}, False),
        ({"min_misses": 100_000}, False),
        ({"min_checkpoints": 100}, False),
        ({"min_seconds": 100}, False),
        ({}, True),
    ],
)
def test_runner_rejects_insufficient_work(graph_factory, overrides, hit_only):
    def request(graph, scenario, index):
        return perform_request(graph, scenario, 0 if hit_only else index)

    with pytest.raises(
        InsufficientPressure, match=r"elapsed_seconds=.*misses=.*checkpoints=.*deadline"
    ):
        measure_pressure(
            graph_factory,
            SCENARIOS[0],
            short_budget(**overrides),
            clock=TickClock(),
            request=request,
        )
    assert not tracemalloc.is_tracing()
    assert FOLIO._basic_search.cache_info().currsize == 0


@pytest.mark.parametrize("during_setup", [True, False])
def test_failure_cleans_owned_instrumentation_and_global_cache(
    graph_factory, during_setup
):
    def fail(*args):
        FOLIO._basic_search("seed", ("seed",))
        raise ValueError("injected failure")

    with pytest.raises(InsufficientPressure, match="injected failure"):
        measure_pressure(
            fail if during_setup else graph_factory,
            "fuzzy-mixed",
            short_budget(),
            request=fail,
        )
    assert not tracemalloc.is_tracing()
    assert FOLIO._basic_search.cache_info().currsize == 0
    assert graph_factory().llm is None


def test_runner_preserves_existing_tracing(graph_factory):
    tracemalloc.start()
    try:
        with pytest.raises(RuntimeError, match="ownership"):
            measure_pressure(graph_factory, SCENARIOS[0], short_budget())
        assert tracemalloc.is_tracing()
    finally:
        tracemalloc.stop()


def test_report_has_bounded_public_fields(graph_factory):
    report = measure_pressure(
        graph_factory, SCENARIOS[0], short_budget(min_checkpoints=25), clock=TickClock()
    )
    assert report["checkpoint_count"] >= 25
    assert len(report["checkpoints"]) == 16
    assert report["batch_timing"]["early"]["batches"] == 8
    assert report["batch_timing"]["late"]["batches"] == 8
    encoded = json.dumps(report, allow_nan=False)
    assert len(encoded) < 10_000
    assert json.loads(encoded) == report
    assert set(report) == {
        "scenario",
        "backend",
        "outcome",
        "dataset",
        "capacity_entries",
        "criteria",
        "elapsed_seconds",
        "requests",
        "misses",
        "hits",
        "result_bearing_requests",
        "capacity_turnovers",
        "checkpoint_count",
        "checkpoints",
        "cache_entries",
        "batch_timing",
        "traced_memory",
    }
