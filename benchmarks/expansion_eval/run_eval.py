"""
Evaluate LLM query expansion + reciprocal rank fusion (``FOLIO.search_expanded``).

Compares, on the labelled natural-language query set in ``queries.json``:

* plain ``search_by_label`` and plain ``search_by_definition``;
* LLM expansion + RRF, replaying the recorded expansions in
  ``llm_expansions.json`` (no network, deterministic) under several fusion
  settings;
* kaos-nlp-core lexicon (OpenGloss synonym/inflection) expansion + RRF, replaying
  ``kaos_lexicon_expansions.json``.

Each is run on every available search backend (RapidFuzz, and kaos BM25 when the
``kaos`` extra is installed).  ``--live`` additionally calls a real LLM
(OpenAI, ``OPENAI_API_KEY``) through ``FOLIO.search_expanded`` to measure cold and
cached end-to-end latency and token usage.

Usage (kaos requires Python >= 3.13):

    uv run --extra kaos python benchmarks/expansion_eval/run_eval.py [--live] [--json out.json]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import statistics
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional

import folio.expansion as fx
from folio import FOLIO, kaos_search

HERE = Path(__file__).parent
BACKENDS = ["rapidfuzz", "kaos"] if kaos_search.KAOS_AVAILABLE else ["rapidfuzz"]


class ReplayLLM:
    """Implements ``json_async`` by replaying recorded expansions."""

    def __init__(self, table: Dict[str, List[str]]) -> None:
        self.table = table

    async def json_async(self, prompt: str, **_: Any) -> Any:
        query = json.loads(prompt.split("# QUERY\n", 1)[1].split("\n", 1)[0])
        return SimpleNamespace(
            data={"expansions": self.table.get(query, [])}, metadata={}
        )


def score(ranked: Dict[str, List[str]], gold: Dict[str, set]) -> Dict[str, float]:
    hit1 = hit5 = mrr = 0.0
    for query, expected in gold.items():
        rank = next(
            (i for i, iri in enumerate(ranked[query][:10], 1) if iri in expected), None
        )
        hit1 += rank == 1
        hit5 += bool(rank and rank <= 5)
        mrr += 1 / rank if rank else 0.0
    n = len(gold)
    return {
        "hit@1": round(hit1 / n, 3),
        "hit@5": round(hit5 / n, 3),
        "mrr": round(mrr / n, 3),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="also call a real LLM")
    parser.add_argument("--model", default="gpt-6.1-terra")
    parser.add_argument("--json", type=Path, help="write results here")
    parser.add_argument("--backend", choices=BACKENDS, action="append")
    args = parser.parse_args()

    spec = json.loads((HERE / "queries.json").read_text())
    gold = {row["query"]: set(row["expected"]) for row in spec["queries"]}
    queries = list(gold)
    llm_table = json.loads((HERE / "llm_expansions.json").read_text())["expansions"]
    kaos_table = json.loads((HERE / "kaos_lexicon_expansions.json").read_text())[
        "expansions"
    ]

    logging.disable(logging.WARNING)  # FOLIO(llm=None) logs a missing default key
    folio = FOLIO(llm=None)
    rows: List[Dict[str, Any]] = []

    def record(name: str, ranked: Dict[str, List[str]], latency: str = "") -> None:
        row = {"method": name, **score(ranked, gold), "latency": latency}
        rows.append(row)
        print(
            f"{name:52s} hit@1 {row['hit@1']:.2f} hit@5 {row['hit@5']:.2f} "
            f"MRR {row['mrr']:.3f} {latency}",
            flush=True,
        )

    def plain(search: Callable[[str], list]) -> None:
        ranked, lat = {}, []
        for query in queries:
            start = time.perf_counter()
            ranked[query] = [c.iri for c, _ in search(query)]
            lat.append(time.perf_counter() - start)
        return ranked, f"p50 {statistics.median(lat) * 1000:.1f} ms"

    async def fused(table: Dict[str, List[str]], **kwargs: Any):
        fx._EXPANDERS.pop(folio, None)  # fresh expansion cache
        folio.llm = ReplayLLM(table)
        ranked, lat = {}, []
        for query in queries:
            start = time.perf_counter()
            result = await fx.search_expanded(folio, query, limit=10, **kwargs)
            lat.append(time.perf_counter() - start)
            ranked[query] = [hit.owl_class.iri for hit in result.hits]
        return ranked, f"p50 {statistics.median(lat) * 1000:.0f} ms (LLM excluded)"

    for backend in args.backend or BACKENDS:
        os.environ[kaos_search.SEARCH_BACKEND_ENV] = (
            "rapidfuzz" if backend == "rapidfuzz" else "auto"
        )
        folio.search_by_label("warm up", limit=1)
        folio.search_by_definition("warm up", limit=1)
        tag = f"[{backend}]"
        record(f"{tag} plain label", *plain(lambda q: folio.search_by_label(q)))
        record(
            f"{tag} plain definition", *plain(lambda q: folio.search_by_definition(q))
        )
        variants = [
            ("defaults", {}),
            (
                "rank-only RRF (score_exponent=0, no decay)",
                dict(score_exponent=0, expansion_decay=0),
            ),
            ("no anchoring (anchor_score=None)", dict(anchor_score=None)),
            ("no definitions", dict(include_definitions=False)),
            ("original_weight=1", dict(original_weight=1.0)),
            ("expansion_decay=0", dict(expansion_decay=0.0)),
            ("score_exponent=1", dict(score_exponent=1.0)),
            ("max_expansions=5", dict(max_expansions=5)),
            ("per_term_limit=20", dict(per_term_limit=20)),
        ]
        for name, kwargs in variants:
            record(f"{tag} LLM+RRF {name}", *await fused(llm_table, **kwargs))
        record(f"{tag} kaos-lexicon+RRF defaults", *await fused(kaos_table))

    live: Optional[Dict[str, Any]] = None
    if args.live:
        from alea_llm_client import OpenAIModel

        folio.llm = OpenAIModel(model=args.model, cache_path=None)
        folio.llm_kwargs = {"reasoning_effort": "low"}
        fx._EXPANDERS.pop(folio, None)
        ranked, cold, cached, prompt_tokens, completion_tokens = {}, [], [], [], []
        for query in queries:
            start = time.perf_counter()
            result = await folio.search_expanded(query)
            cold.append(time.perf_counter() - start)
            start = time.perf_counter()
            await folio.search_expanded(query)
            cached.append(time.perf_counter() - start)
            ranked[query] = [hit.owl_class.iri for hit in result.hits]
            prompt_tokens.append(result.usage.get("prompt_tokens", 0))
            completion_tokens.append(result.usage.get("completion_tokens", 0))
        cold.sort()
        record(
            f"[{BACKENDS[-1]}] LIVE search_expanded defaults",
            ranked,
            f"cold p50 {statistics.median(cold):.2f} s p90 {cold[int(0.9 * len(cold))]:.2f} s; "
            f"cached p50 {statistics.median(cached) * 1000:.1f} ms",
        )
        live = {
            "prompt_tokens_mean": statistics.mean(prompt_tokens),
            "completion_tokens_mean": statistics.mean(completion_tokens),
        }
        print(live)

    if args.json:
        args.json.write_text(json.dumps({"rows": rows, "live": live}, indent=2) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
