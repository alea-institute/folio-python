"""Query expansion + reciprocal rank fusion, exercised without a provider."""

import asyncio
from types import SimpleNamespace

import pytest

import folio.expansion as fx
from folio.expansion import (
    QueryExpander,
    normalize_query,
    parse_expansions,
    reciprocal_rank_fusion,
)

BASE = "https://folio.openlegalstandard.org/"
HABITABILITY = BASE + "RHabitability"
LANDLORD = BASE + "RLandlord"
NEGLIGENCE = BASE + "RNegligence"
EVICTION = BASE + "REviction"


class FakeLLM:
    def __init__(self, *responses, delay=0.0):
        self.responses = list(responses)
        self.delay = delay
        self.calls = []

    async def json_async(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        if self.delay:
            await asyncio.sleep(self.delay)
        response = (
            self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        )
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(data=response, metadata={"usage": {"prompt_tokens": 10}})


@pytest.fixture
def graph(local_graph):
    return local_graph(f'''
        <owl:Class rdf:about="{HABITABILITY}">
            <rdfs:label>Breach of Implied Warranty of Habitability</rdfs:label>
        </owl:Class>
        <owl:Class rdf:about="{LANDLORD}"><rdfs:label>Landlord</rdfs:label></owl:Class>
        <owl:Class rdf:about="{NEGLIGENCE}">
            <rdfs:label>Landlord Negligence</rdfs:label>
        </owl:Class>
        <owl:Class rdf:about="{EVICTION}">
            <rdfs:label>Constructive Eviction of Tenant</rdfs:label>
        </owl:Class>
    ''')


def test_normalize_query():
    assert normalize_query("  Non-Compete  Enforceability ") == (
        "non-compete enforceability"
    )
    assert normalize_query("") == ""


@pytest.mark.parametrize(
    "payload",
    [
        {"expansions": ["Warranty of Habitability", "Landlord Negligence"]},
        {"terms": ["Warranty of Habitability", "Landlord Negligence"]},
        {"anything": ["Warranty of Habitability", "Landlord Negligence"]},
        ["Warranty of Habitability", "Landlord Negligence"],
        '{"expansions": ["Warranty of Habitability", "Landlord Negligence"]}',
        [{"term": "Warranty of Habitability"}, {"text": "Landlord Negligence"}],
    ],
)
def test_parse_expansions_shapes(payload):
    assert parse_expansions(payload, "heat") == [
        "Warranty of Habitability",
        "Landlord Negligence",
    ]


def test_parse_expansions_cleans_dedupes_caps_and_drops_query():
    payload = [
        "1. Warranty of Habitability.",
        "- warranty of habitability",
        '"Landlord-Tenant Law"',
        "Landlord Tenant Law",
        "No Heat",
        "no heat!",
        "x" * 200,
        "one two three four five six seven eight nine",
        "   ",
        "???",
        42,
        None,
        "Constructive Eviction",
    ]
    assert parse_expansions(payload, "No heat") == [
        "Warranty of Habitability",
        "Landlord-Tenant Law",
        "Constructive Eviction",
    ]
    assert parse_expansions(payload, "q", max_expansions=1) == [
        "Warranty of Habitability"
    ]


@pytest.mark.parametrize(
    "payload", [None, {}, "not json", 7, {"a": [1], "b": [2]}, {"expansions": "x"}]
)
def test_parse_expansions_garbage(payload):
    assert parse_expansions(payload, "q") == []


def test_reciprocal_rank_fusion_weights_and_matched_via():
    fused = reciprocal_rank_fusion(
        [
            ("query", 2.0, ["a", "b", "a"]),
            ("syn1", 1.0, ["b", "c"]),
            ("syn2", 1.0, ["b"]),
            ("ignored", 0.0, ["z"]),
        ],
        k=60,
    )
    scores = {iri: score for iri, score, _ in fused}
    assert [iri for iri, _, _ in fused] == ["b", "a", "c"]
    assert scores["a"] == pytest.approx(2 / 61)
    assert scores["b"] == pytest.approx(2 / 62 + 1 / 61 + 1 / 61)
    assert scores["c"] == pytest.approx(1 / 62)
    assert fused[0][2] == ["query", "syn1", "syn2"]
    assert "z" not in scores
    assert reciprocal_rank_fusion([]) == []


@pytest.mark.asyncio
async def test_expander_caches_normalised_query_and_slices():
    expander = QueryExpander(cache_size=2)
    llm = FakeLLM({"expansions": ["A", "B", "C", "D", "E", "F"]})
    first = await expander.expand_with_outcome("Heat ", llm, {"temperature": 0})
    assert first.source == "llm"
    assert first.expansions == ["A", "B", "C", "D", "E", "F"]
    assert first.usage == {"prompt_tokens": 10}
    assert llm.calls[0][1]["temperature"] == 0
    assert '"Heat"' in llm.calls[0][0]
    again = await expander.expand_with_outcome("  heat", llm, max_expansions=2)
    assert (again.source, again.expansions) == ("cache", ["A", "B"])
    assert len(llm.calls) == 1
    # LRU eviction
    await expander.expand("q2", llm)
    await expander.expand("q3", llm)
    assert expander.cache_get("heat") is None
    assert expander.cache_get("q3") is not None
    expander.clear()
    assert expander.cache_get("q3") is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "llm, error",
    [
        (None, "llm unavailable"),
        (object(), "llm unavailable"),
        (FakeLLM(RuntimeError("provider down")), "RuntimeError"),
        (FakeLLM({"expansions": ["heat"]}), "invalid response"),
        (FakeLLM("garbage"), "invalid response"),
        (FakeLLM({"expansions": ["A"]}, delay=1.0), "timeout"),
    ],
)
async def test_expander_never_raises(llm, error):
    expander = QueryExpander()
    outcome = await expander.expand_with_outcome("heat", llm, timeout=0.05)
    assert outcome.expansions == []
    assert outcome.source == "none"
    assert outcome.error == error
    # failures are not cached
    assert expander.cache_get("heat") is None


@pytest.mark.asyncio
async def test_expander_zero_or_empty_skips_llm():
    llm = FakeLLM({"expansions": ["A"]})
    expander = QueryExpander()
    assert await expander.expand("heat", llm, max_expansions=0) == []
    assert await expander.expand("   ", llm) == []
    assert llm.calls == []


@pytest.mark.asyncio
async def test_expander_circuit_breaker(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(fx.time, "monotonic", lambda: clock[0])
    expander = QueryExpander(failure_threshold=2, cooldown_seconds=30)
    failing = FakeLLM(RuntimeError("down"))
    await expander.expand("a", failing)
    await expander.expand("b", failing)
    assert expander.circuit_open
    outcome = await expander.expand_with_outcome("c", failing)
    assert outcome.error == "llm circuit open"
    assert len(failing.calls) == 2
    clock[0] += 31
    assert not expander.circuit_open
    healthy = FakeLLM({"expansions": ["X"]})
    assert await expander.expand("c", healthy) == ["X"]


@pytest.mark.asyncio
async def test_expander_shares_inflight_call():
    llm = FakeLLM({"expansions": ["A", "B"]}, delay=0.05)
    expander = QueryExpander()
    results = await asyncio.gather(*(expander.expand("heat", llm) for _ in range(5)))
    assert results == [["A", "B"]] * 5
    assert len(llm.calls) == 1


@pytest.mark.asyncio
async def test_search_expanded_fuses_expansions(graph):
    graph.llm = FakeLLM(
        {"expansions": ["Warranty of Habitability", "Landlord Negligence"]}
    )
    graph.llm_kwargs = {"reasoning_effort": "low"}
    result = await graph.search_expanded("my landlord won't fix the heat", limit=3)
    assert result.expansion_source == "llm"
    assert result.expansions == ["Warranty of Habitability", "Landlord Negligence"]
    assert len(result.hits) == 3
    assert graph.llm.calls[0][1]["reasoning_effort"] == "low"
    by_iri = {hit.owl_class.iri: hit for hit in result.hits}
    assert "Landlord Negligence" in by_iri[NEGLIGENCE].matched_via
    assert all(hit.score > 0 for hit in result.hits)
    assert [hit.score for hit in result.hits] == sorted(
        (hit.score for hit in result.hits), reverse=True
    )
    payload = result.to_dict()
    assert payload["expansions"] == result.expansions
    assert payload["results"][0]["iri"] == result.hits[0].owl_class.iri

    cached = await graph.search_expanded(
        "My landlord won't fix the heat", include_definitions=True
    )
    assert cached.expansion_source == "cache"
    assert len(graph.llm.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "llm",
    [None, FakeLLM(RuntimeError("down")), FakeLLM({"nope": 1}), FakeLLM("garbage")],
)
async def test_search_expanded_degrades_to_plain_label_search(graph, llm):
    graph.llm = llm
    result = await graph.search_expanded("Landlord", limit=2)
    assert result.expansions == []
    assert result.expansion_source == "none"
    plain = [
        owl_class.iri for owl_class, _ in graph.search_by_label("Landlord", limit=10)
    ][:2]
    assert [hit.owl_class.iri for hit in result.hits] == plain
    assert all(hit.matched_via == ["Landlord"] for hit in result.hits)


@pytest.mark.asyncio
async def test_search_expanded_skips_failing_expansion_search(graph, monkeypatch):
    graph.llm = FakeLLM({"expansions": ["boom", "Landlord Negligence"]})
    original = graph.search_by_label

    def flaky(label, **kwargs):
        if label == "boom":
            raise ValueError("backend hiccup")
        return original(label, **kwargs)

    monkeypatch.setattr(graph, "search_by_label", flaky)
    result = await graph.search_expanded("heat")
    assert result.hits
    assert all("boom" not in hit.matched_via for hit in result.hits)


@pytest.mark.asyncio
async def test_search_expanded_empty_query(graph):
    graph.llm = FakeLLM({"expansions": ["A"]})
    result = await graph.search_expanded("   ")
    assert (result.hits, result.expansions, result.expansion_source) == ([], [], "none")
    assert graph.llm.calls == []


def test_reciprocal_rank_fusion_score_weighting():
    lists = [
        ("query", 1.0, [("weak", 50.0), ("strong", 100.0)]),
        ("syn", 1.0, [("strong", 100.0), ("none", None), ("zero", 0.0)]),
    ]
    plain = reciprocal_rank_fusion(lists, k=60)
    weighted = reciprocal_rank_fusion(lists, k=60, score_exponent=2.0)
    assert dict((i, s) for i, s, _ in plain)["weak"] == pytest.approx(1 / 61)
    scores = {iri: score for iri, score, _ in weighted}
    assert scores["weak"] == pytest.approx(0.25 / 61)
    assert scores["strong"] == pytest.approx(1 / 62 + 1 / 61)
    assert scores["none"] == pytest.approx(1 / 62)  # unknown score counts fully
    assert "zero" not in scores
    assert [iri for iri, _, _ in weighted][0] == "strong"


@pytest.mark.asyncio
async def test_search_expanded_anchors_exact_original_match(graph):
    graph.llm = FakeLLM(
        {"expansions": ["Landlord Negligence", "Negligence", "Landlord Negligence Law"]}
    )
    anchored = await graph.search_expanded("Landlord", limit=4)
    assert anchored.hits[0].owl_class.iri == LANDLORD
    unanchored = await fx.search_expanded(graph, "Landlord", limit=4, anchor_score=None)
    assert unanchored.hits[0].owl_class.iri == NEGLIGENCE
    assert {hit.owl_class.iri for hit in anchored.hits} == {
        hit.owl_class.iri for hit in unanchored.hits
    }
