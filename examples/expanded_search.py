"""Expand a natural-language query and inspect the resulting ontology hits.

From a checkout with the search extra installed, run:
    uv run --frozen python examples/expanded_search.py

The demo LLM returns fixed terms for the sample query; it makes no provider call
and needs no API key. Running the script may download the public ontology.
Importing it does not construct a graph. For real query expansion, pass your
already initialized FOLIO graph with a configured LLM to expanded_search().
"""

import asyncio
from types import SimpleNamespace

from folio import FOLIO
from folio.expansion import ExpandedSearchResult


class DemoLLM:
    """A fixed response for the heat-repair example, not a general query model."""

    async def json_async(self, prompt, **kwargs):
        return SimpleNamespace(
            data={"expansions": ["Warranty of Habitability", "Landlord Negligence"]}
        )


async def expanded_search(
    graph: FOLIO,
    query: str,
    *,
    limit: int = 10,
    include_definitions: bool = True,
    max_expansions: int = 8,
    timeout: float = 10.0,
) -> ExpandedSearchResult:
    """Return real search results using the graph's LLM and search backend.

    Set max_expansions=0 to search only the original query. Definitions are
    searched too unless include_definitions=False. Use a positive limit.
    """
    return await graph.search_expanded(
        query,
        limit=limit,
        include_definitions=include_definitions,
        max_expansions=max_expansions,
        timeout=timeout,
    )


async def main():
    graph = FOLIO(llm=DemoLLM())
    result = await expanded_search(graph, "my landlord won't fix the heat")
    print(f"Expansion source: {result.expansion_source}")
    print(f"Expansion terms: {result.expansions}")
    # Hits depend on the ontology and search backend, even with fixed terms.
    for hit in result.hits:
        print(f"{hit.owl_class.label} ({hit.owl_class.iri})")
        print(f"  Fusion score: {hit.score:.4f}; matched via: {hit.matched_via}")


if __name__ == "__main__":
    asyncio.run(main())
