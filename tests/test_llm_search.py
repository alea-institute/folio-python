"""LLM response contracts, exercised without a provider or credentials."""

from types import SimpleNamespace

import pytest

import folio.graph


FIRST = "https://folio.openlegalstandard.org/Rfirst"
SECOND = "https://folio.openlegalstandard.org/Rsecond"


@pytest.fixture
def llm_graph(local_graph, monkeypatch):
    graph = local_graph(f'''
        <owl:Class rdf:about="{FIRST}"><rdfs:label>First</rdfs:label></owl:Class>
        <owl:Class rdf:about="{SECOND}"><rdfs:label>Second</rdfs:label></owl:Class>
    ''')
    # Isolate optional prompt helpers along with the provider boundary.
    monkeypatch.setattr(
        folio.graph, "format_prompt", lambda sections: sections, raising=False
    )
    monkeypatch.setattr(
        folio.graph,
        "format_instructions",
        lambda items: "\n".join(items),
        raising=False,
    )
    return graph


class FakeModel:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.requests = []

    async def json_async(self, prompt, **kwargs):
        self.requests.append((prompt, kwargs))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(data=response)


@pytest.mark.asyncio
@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("include_reason", [False, True])
async def test_llm_payload_filter_sort_limit_and_tuple_shape(
    llm_graph, wrapped, include_reason
):
    payload = [
        {"iri": FIRST, "relevance": 4, "explanation": "First reason"},
        {"iri": "https://example.org/unknown", "relevance": 10},
        {"iri": SECOND, "relevance": 9, "explanation": "Second reason"},
        {"iri": FIRST, "relevance": 8, "explanation": "Duplicate"},
        {"relevance": 10},
    ]
    llm_graph.llm = FakeModel({"results": payload} if wrapped else payload)
    llm_graph.llm_kwargs = {"temperature": 0}
    result = await llm_graph.search_by_llm(
        "question", llm_graph.classes, limit=2, include_reason=include_reason
    )
    expected = [(llm_graph[SECOND], 9), (llm_graph[FIRST], 4)]
    if include_reason:
        expected = [
            (*row, reason)
            for row, reason in zip(expected, ("Second reason", "First reason"))
        ]
    assert result == expected
    assert llm_graph.llm.requests[0][0]["query"] == "question"
    assert llm_graph.llm.requests[0][1]["temperature"] == 0
    llm_graph.llm = FakeModel(payload)
    assert (
        len(await llm_graph.search_by_llm("question", llm_graph.classes, limit=1)) == 1
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [None, {}, "invalid", {"results": []}])
async def test_empty_or_unrecognized_llm_payload(llm_graph, response):
    llm_graph.llm = FakeModel(response)
    assert await llm_graph.search_by_llm("question", llm_graph.classes) == []


@pytest.mark.asyncio
async def test_llm_defaults_for_missing_score_and_reason(llm_graph):
    llm_graph.llm = FakeModel([{"iri": FIRST}])
    assert await llm_graph.search_by_llm(
        "question", llm_graph.classes, include_reason=True
    ) == [(llm_graph[FIRST], 0, "")]


@pytest.mark.asyncio
@pytest.mark.parametrize("parallel", [False, True])
async def test_absent_llm_retains_missing_extra_error(llm_graph, parallel):
    llm_graph.llm = None
    with pytest.raises(RuntimeError, match="search extra must be installed"):
        if parallel:
            await llm_graph.parallel_search_by_llm("question", [llm_graph.classes])
        else:
            await llm_graph.search_by_llm("question", llm_graph.classes)


@pytest.mark.asyncio
@pytest.mark.parametrize("parallel", [False, True])
async def test_provider_exception_is_wrapped(llm_graph, parallel):
    error = ValueError("provider unavailable")
    llm_graph.llm = FakeModel(error)
    with pytest.raises(RuntimeError, match="Error searching with LLM") as caught:
        if parallel:
            await llm_graph.parallel_search_by_llm("question", [llm_graph.classes])
        else:
            await llm_graph.search_by_llm("question", llm_graph.classes)
    cause = caught.value.__cause__
    assert (cause.__cause__ if parallel else cause) is error


@pytest.mark.asyncio
@pytest.mark.parametrize("include_reason", [False, True])
async def test_parallel_search_globally_sorts_and_limits(llm_graph, include_reason):
    first = {"iri": FIRST, "relevance": 2, "explanation": "First reason"}
    second = {"iri": SECOND, "relevance": 8, "explanation": "Second reason"}
    llm_graph.llm = FakeModel([first], {"results": [second]})
    result = await llm_graph.parallel_search_by_llm(
        "question",
        [[llm_graph[FIRST]], [llm_graph[SECOND]]],
        limit=1,
        include_reason=include_reason,
    )
    expected = (
        (llm_graph[SECOND], 8, "Second reason")
        if include_reason
        else (llm_graph[SECOND], 8)
    )
    assert result == [expected]
    assert len(llm_graph.llm.requests) == 2
