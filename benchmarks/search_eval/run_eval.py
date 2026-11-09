"""
Evaluate FOLIO label/definition search against the labelled query set.

Compares the RapidFuzz backend with the kaos-nlp-core backend through the
public ``FOLIO.search_by_label`` / ``FOLIO.search_by_definition`` API on the
real FOLIO graph, reporting hit@1, hit@5, MRR, per-query latency and the worst
asyncio event-loop stall while the queries run concurrently in worker threads.

Usage (kaos requires Python >= 3.13):

    uv run --python 3.13 python benchmarks/search_eval/run_eval.py [--json out.json]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List

from folio import FOLIO
from folio import kaos_search

QUERIES = Path(__file__).with_name("queries.json")
BACKENDS = ["rapidfuzz", "kaos"] if kaos_search.KAOS_AVAILABLE else ["rapidfuzz"]


def set_backend(name: str) -> None:
    os.environ[kaos_search.SEARCH_BACKEND_ENV] = name


def percentile(values: List[float], pct: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(pct * (len(ordered) - 1)))]


def evaluate(search: Callable[[str], List[Any]], queries: List[dict]) -> dict:
    hit1 = hit5 = 0
    reciprocal = 0.0
    latencies: List[float] = []
    by_category: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    ranks: Dict[str, Any] = {}
    for item in queries:
        expected = {e["iri"] for e in item["expected"]}
        start = time.perf_counter()
        results = search(item["query"])
        latencies.append((time.perf_counter() - start) * 1000)
        iris = [owl_class.iri for owl_class, _ in results]
        rank = next((i + 1 for i, iri in enumerate(iris) if iri in expected), None)
        hit1 += rank == 1
        hit5 += rank is not None and rank <= 5
        reciprocal += 1.0 / rank if rank else 0.0
        by_category[item["category"]][0] += rank is not None and rank <= 5
        by_category[item["category"]][1] += 1
        ranks[item["query"]] = {
            "rank": rank,
            "top3": [(c.label, s) for c, s in results[:3]],
        }
    n = len(queries)
    return {
        "n": n,
        "hit@1": round(hit1 / n, 3),
        "hit@5": round(hit5 / n, 3),
        "mrr": round(reciprocal / n, 3),
        "p50_ms": round(statistics.median(latencies), 2),
        "p95_ms": round(percentile(latencies, 0.95), 2),
        "hit@5_by_category": {k: f"{a}/{b}" for k, (a, b) in by_category.items()},
        "ranks": ranks,
    }


async def loop_stall(fns: List[Callable[[], Any]]) -> dict:
    """Run ``fns`` in worker threads; measure the worst 1 ms-ticker overrun."""
    worst = 0.0
    done = False

    async def ticker() -> None:
        nonlocal worst
        while not done:
            start = time.perf_counter()
            await asyncio.sleep(0.001)
            worst = max(worst, time.perf_counter() - start - 0.001)

    task = asyncio.create_task(ticker())
    await asyncio.sleep(0.01)
    start = time.perf_counter()
    await asyncio.gather(*(asyncio.to_thread(fn) for fn in fns))
    elapsed = time.perf_counter() - start
    done = True
    await task
    return {
        "threads_total_ms": round(elapsed * 1000, 1),
        "worst_stall_ms": round(worst * 1000, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write full results here")
    args = parser.parse_args()

    data = json.loads(QUERIES.read_text(encoding="utf-8"))
    folio = FOLIO(llm=None)
    report: Dict[str, Any] = {"kaos_available": kaos_search.KAOS_AVAILABLE}

    for backend in BACKENDS:
        # fresh graph state per backend: no warm caches carried across backends
        folio._kaos_indices.clear()  # pylint: disable=protected-access
        FOLIO._basic_search.cache_clear()  # pylint: disable=protected-access
        set_backend(backend)
        start = time.perf_counter()
        folio.search_by_label("warm up index")
        folio.search_by_definition("warm up index")
        warm_ms = round((time.perf_counter() - start) * 1000, 1)
        FOLIO._basic_search.cache_clear()  # pylint: disable=protected-access

        label = evaluate(folio.search_by_label, data["label_queries"])
        definition = evaluate(folio.search_by_definition, data["definition_queries"])

        # stall test with distinct queries (defeats the RapidFuzz lru_cache)
        FOLIO._basic_search.cache_clear()  # pylint: disable=protected-access
        label_fns = [
            (lambda q=q["query"]: folio.search_by_label(q))
            for q in data["label_queries"][:20]
        ]
        def_fns = [
            (lambda q=q["query"]: folio.search_by_definition(q))
            for q in data["definition_queries"][:20]
        ]
        report[backend] = {
            "first_call_incl_index_build_ms": warm_ms,
            "label": label,
            "definition": definition,
            "stall_label_20_threads": asyncio.run(loop_stall(label_fns)),
            "stall_definition_20_threads": asyncio.run(loop_stall(def_fns)),
        }

    print(
        f"{'backend':10} {'kind':10} {'n':>3} {'hit@1':>6} {'hit@5':>6} {'MRR':>6} "
        f"{'p50ms':>7} {'p95ms':>7} {'stall ms':>8}"
    )
    for backend in BACKENDS:
        for kind in ("label", "definition"):
            r = report[backend][kind]
            stall = report[backend][f"stall_{kind}_20_threads"]["worst_stall_ms"]
            print(
                f"{backend:10} {kind:10} {r['n']:>3} {r['hit@1']:>6} {r['hit@5']:>6} "
                f"{r['mrr']:>6} {r['p50_ms']:>7} {r['p95_ms']:>7} {stall:>8}"
            )
        print(
            f"{backend:10} first call (incl. index build): {report[backend]['first_call_incl_index_build_ms']} ms"
        )
        print(
            f"{backend:10} label hit@5 by category: {report[backend]['label']['hit@5_by_category']}"
        )

    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
