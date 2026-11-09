"""
folio/expansion.py - LLM query expansion and rank fusion for FOLIO search.

A natural-language query such as "my landlord won't fix the heat" rarely matches
an ontology label directly.  This module asks an LLM for a handful of synonyms,
legal terms of art and closely related concepts ("warranty of habitability",
"landlord negligence", ...), searches FOLIO for the original query and every
expansion, and merges the ranked lists with weighted reciprocal rank fusion
(RRF).

Design points:

* ``QueryExpander.expand`` never raises: a missing/disabled LLM, a provider
  error, a timeout or an unparseable response all yield an empty expansion
  list, so callers degrade to plain search.
* Successful expansions are kept in a bounded LRU cache keyed on the
  normalised query; identical concurrent requests share one LLM call.
* Repeated failures open a short circuit breaker so an LLM outage costs
  nothing but a log line instead of a timeout per request.
* Per-term searches go through the public ``FOLIO.search_by_label`` /
  ``FOLIO.search_by_definition`` methods in a worker thread, so the event loop
  is never blocked and the search backend can change independently.
"""

# future import for self-referencing type hints
from __future__ import annotations

# imports
import asyncio
import json
import re
import threading
import time
import unicodedata
import weakref
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
)

# project imports
from folio.logger import get_logger

if TYPE_CHECKING:
    from folio.graph import FOLIO
    from folio.models import OWLClass

LOGGER = get_logger(__name__)

# expansion defaults
DEFAULT_MAX_EXPANSIONS = 8
MAX_EXPANSIONS = 10
DEFAULT_EXPANSION_TIMEOUT = 10.0
DEFAULT_EXPANSION_CACHE_SIZE = 2048
MAX_QUERY_CHARS = 500
MAX_EXPANSION_CHARS = 80
MAX_EXPANSION_WORDS = 8

# circuit breaker defaults
DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_COOLDOWN_SECONDS = 30.0

# fusion defaults
DEFAULT_RRF_K = 60
DEFAULT_ORIGINAL_WEIGHT = 2.0
DEFAULT_EXPANSION_WEIGHT = 1.0
DEFAULT_EXPANSION_DECAY = 0.3
DEFAULT_DEFINITION_WEIGHT = 0.5
DEFAULT_SCORE_EXPONENT = 2.0
DEFAULT_INCLUDE_DEFINITIONS = True
DEFAULT_PER_TERM_LIMIT = 10
DEFAULT_ANCHOR_SCORE = 92.0
MAX_ANCHORS = 3
MAX_SEARCH_SCORE = 100.0

ExpansionSource = Literal["llm", "cache", "none"]

EXPANSION_SYSTEM_PROMPT = (
    "You are a legal research assistant that expands search queries for FOLIO, "
    "a legal ontology of areas of law, claims and causes of action, legal documents, "
    "actors, events and other legal concepts. Always respond in JSON according to SCHEMA."
)

EXPANSION_INSTRUCTIONS = (
    "Rewrite the QUERY below as search terms that would match concept names in a legal taxonomy.",
    "Return between 5 and 10 distinct terms.",
    "Include synonyms, legal terms of art, the names of relevant claims or causes of action, "
    "areas of law, and closely related legal concepts or phrases.",
    "Prefer short canonical names a legal taxonomy would use (for example "
    '"Adverse Possession" or "Breach of Lease"), not sentences.',
    "Each term must be 1 to 6 words. No explanations, numbering or citations.",
    "Do not repeat the query itself.",
)

EXPANSION_SCHEMA = '{"expansions": [string, ...]}'

_LIST_KEYS = ("expansions", "terms", "queries", "synonyms", "results", "items")
_BULLET_RE = re.compile(r"^\s*(?:[-*•]+|\d{1,2}[.):])\s*")
_SPACE_RE = re.compile(r"\s+")
_KEY_STRIP_RE = re.compile(r"[^\w]+")
_EDGE_PUNCT = " \t\"'`“”‘’.,;:!?()[]{}"


def normalize_query(query: str) -> str:
    """
    Normalise a query for cache keys and duplicate detection.

    Args:
        query (str): The raw query.

    Returns:
        str: NFKC-normalised, whitespace-collapsed, case-folded query.
    """
    text = unicodedata.normalize("NFKC", query or "")
    return _SPACE_RE.sub(" ", text).strip().casefold()


def _term_key(term: str) -> str:
    """Comparison key that ignores case, punctuation and spacing."""
    return _KEY_STRIP_RE.sub("", normalize_query(term))


def _clean_term(value: Any) -> Optional[str]:
    """Clean one candidate expansion; return None if it is unusable."""
    if isinstance(value, dict):
        value = next(
            (value[key] for key in ("term", "text", "label", "query") if key in value),
            None,
        )
    if not isinstance(value, str):
        return None
    text = unicodedata.normalize("NFKC", value)
    text = _BULLET_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip(_EDGE_PUNCT).strip()
    if not text or len(text) > MAX_EXPANSION_CHARS:
        return None
    if len(text.split()) > MAX_EXPANSION_WORDS:
        return None
    if not any(char.isalnum() for char in text):
        return None
    return text


def parse_expansions(
    data: Any, query: str, max_expansions: int = MAX_EXPANSIONS
) -> List[str]:
    """
    Validate and normalise an LLM expansion payload.

    Accepts a JSON list, a JSON object holding a list (``expansions``, ``terms``,
    ...), or a JSON string of either.  Items are stripped of bullets, quotes and
    surrounding punctuation, length-capped, de-duplicated (case/punctuation
    insensitive) and the original query is dropped.

    Args:
        data (Any): The decoded LLM response.
        query (str): The original query.
        max_expansions (int): The maximum number of expansions to keep.

    Returns:
        List[str]: The cleaned expansions (possibly empty).
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except ValueError:
            return []
    if isinstance(data, dict):
        candidates = next(
            (data[key] for key in _LIST_KEYS if isinstance(data.get(key), list)),
            None,
        )
        if candidates is None:
            lists = [value for value in data.values() if isinstance(value, list)]
            candidates = lists[0] if len(lists) == 1 else []
        data = candidates
    if not isinstance(data, list):
        return []

    seen = {_term_key(query)}
    expansions: List[str] = []
    for item in data:
        term = _clean_term(item)
        if term is None:
            continue
        key = _term_key(term)
        if not key or key in seen:
            continue
        seen.add(key)
        expansions.append(term)
        if len(expansions) >= max(0, max_expansions):
            break
    return expansions


def build_expansion_prompt(query: str) -> str:
    """
    Build the user prompt for query expansion.

    Args:
        query (str): The (already length-capped) query.

    Returns:
        str: The prompt text.
    """
    instructions = "\n".join(f"- {line}" for line in EXPANSION_INSTRUCTIONS)
    return (
        f"# INSTRUCTIONS\n{instructions}\n\n"
        f"# QUERY\n{json.dumps(query, ensure_ascii=False)}\n\n"
        f"# SCHEMA\n{EXPANSION_SCHEMA}\n"
    )


@dataclass
class ExpansionOutcome:
    """Expansions plus how they were obtained."""

    expansions: List[str]
    source: ExpansionSource
    error: Optional[str] = None
    usage: Dict[str, Any] = field(default_factory=dict)


class QueryExpander:
    """
    Cached, timeout-bounded, failure-tolerant LLM query expander.

    The expander holds no reference to an LLM; the model and its kwargs are
    passed per call so that ``FOLIO.llm`` can be swapped at runtime.
    """

    def __init__(
        self,
        cache_size: int = DEFAULT_EXPANSION_CACHE_SIZE,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
    ) -> None:
        """
        Initialise the expander.

        Args:
            cache_size (int): Maximum number of cached queries (LRU eviction).
            failure_threshold (int): Consecutive failures that open the breaker.
            cooldown_seconds (float): How long the breaker stays open.
        """
        self.cache_size = max(0, cache_size)
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self._cache: OrderedDict[str, Tuple[str, ...]] = OrderedDict()
        self._lock = threading.Lock()
        self._inflight: Dict[Tuple[int, str], asyncio.Future[ExpansionOutcome]] = {}
        self._consecutive_failures = 0
        self._open_until = 0.0

    def cache_get(self, key: str) -> Optional[Tuple[str, ...]]:
        """Return cached expansions for a normalised query, refreshing recency."""
        with self._lock:
            value = self._cache.get(key)
            if value is not None:
                self._cache.move_to_end(key)
            return value

    def cache_put(self, key: str, expansions: Sequence[str]) -> None:
        """Store expansions for a normalised query, evicting the oldest entry."""
        if self.cache_size == 0:
            return
        with self._lock:
            self._cache[key] = tuple(expansions)
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear the cache and reset the circuit breaker."""
        with self._lock:
            self._cache.clear()
            self._consecutive_failures = 0
            self._open_until = 0.0

    @property
    def circuit_open(self) -> bool:
        """Whether LLM calls are currently being skipped after repeated failures."""
        return time.monotonic() < self._open_until

    def _record(self, success: bool) -> None:
        with self._lock:
            if success:
                self._consecutive_failures = 0
                self._open_until = 0.0
                return
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._open_until = time.monotonic() + self.cooldown_seconds
                LOGGER.warning(
                    "Query expansion disabled for %.0fs after %d consecutive failures",
                    self.cooldown_seconds,
                    self._consecutive_failures,
                )

    async def expand(
        self,
        query: str,
        llm: Any,
        llm_kwargs: Optional[dict] = None,
        max_expansions: int = DEFAULT_MAX_EXPANSIONS,
        timeout: float = DEFAULT_EXPANSION_TIMEOUT,
    ) -> List[str]:
        """
        Expand a query into related legal search terms.

        Never raises; returns an empty list when expansion is unavailable.

        Args:
            query (str): The user query.
            llm (Any): An object with an async ``json_async(prompt, **kwargs)``
                method (an alea_llm_client model), or None to disable.
            llm_kwargs (Optional[dict]): Extra kwargs for the LLM call.
            max_expansions (int): Maximum expansions to return (0-10).
            timeout (float): Hard timeout in seconds for the LLM call.

        Returns:
            List[str]: The expansions.
        """
        outcome = await self.expand_with_outcome(
            query, llm, llm_kwargs, max_expansions, timeout
        )
        return outcome.expansions

    async def expand_with_outcome(
        self,
        query: str,
        llm: Any,
        llm_kwargs: Optional[dict] = None,
        max_expansions: int = DEFAULT_MAX_EXPANSIONS,
        timeout: float = DEFAULT_EXPANSION_TIMEOUT,
    ) -> ExpansionOutcome:
        """
        Like :meth:`expand` but also reports the source, error and token usage.

        Args:
            query (str): The user query.
            llm (Any): The LLM object, or None to disable expansion.
            llm_kwargs (Optional[dict]): Extra kwargs for the LLM call.
            max_expansions (int): Maximum expansions to return (0-10).
            timeout (float): Hard timeout in seconds for the LLM call.

        Returns:
            ExpansionOutcome: The expansions and metadata.
        """
        limit = min(max(int(max_expansions), 0), MAX_EXPANSIONS)
        key = normalize_query(query)[:MAX_QUERY_CHARS]
        if limit == 0 or not key:
            return ExpansionOutcome([], "none")

        cached = self.cache_get(key)
        if cached is not None:
            return ExpansionOutcome(list(cached[:limit]), "cache")

        if llm is None or not callable(getattr(llm, "json_async", None)):
            return ExpansionOutcome([], "none", "llm unavailable")
        if self.circuit_open:
            return ExpansionOutcome([], "none", "llm circuit open")

        # share one in-flight call between identical concurrent requests
        loop = asyncio.get_running_loop()
        flight_key = (id(loop), key)
        pending = self._inflight.get(flight_key)
        if pending is not None:
            outcome = await asyncio.shield(pending)
            return ExpansionOutcome(
                outcome.expansions[:limit],
                "cache" if outcome.source == "llm" else outcome.source,
                outcome.error,
            )

        future: asyncio.Future[ExpansionOutcome] = loop.create_future()
        self._inflight[flight_key] = future
        try:
            outcome = await self._call_llm(query, key, llm, llm_kwargs or {}, timeout)
        except BaseException as error:  # cancellation: wake waiters, then re-raise
            if not future.done():
                future.set_result(ExpansionOutcome([], "none", repr(error)))
            raise
        finally:
            self._inflight.pop(flight_key, None)
        if not future.done():
            future.set_result(outcome)
        return ExpansionOutcome(
            outcome.expansions[:limit], outcome.source, outcome.error, outcome.usage
        )

    async def _call_llm(
        self, query: str, key: str, llm: Any, llm_kwargs: dict, timeout: float
    ) -> ExpansionOutcome:
        prompt = build_expansion_prompt(
            unicodedata.normalize("NFKC", query).strip()[:MAX_QUERY_CHARS]
        )
        try:
            response = await asyncio.wait_for(
                llm.json_async(prompt, system=EXPANSION_SYSTEM_PROMPT, **llm_kwargs),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            LOGGER.warning("Query expansion timed out after %.1fs", timeout)
            self._record(False)
            return ExpansionOutcome([], "none", "timeout")
        except Exception as error:  # pylint: disable=broad-except
            LOGGER.warning("Query expansion failed: %r", error)
            self._record(False)
            return ExpansionOutcome([], "none", type(error).__name__)

        self._record(True)
        expansions = parse_expansions(
            getattr(response, "data", None), query, MAX_EXPANSIONS
        )
        metadata = getattr(response, "metadata", None)
        usage = metadata.get("usage", {}) if isinstance(metadata, dict) else {}
        if not expansions:
            LOGGER.warning("Query expansion returned no usable terms")
            return ExpansionOutcome([], "none", "invalid response", usage or {})
        self.cache_put(key, expansions)
        return ExpansionOutcome(expansions, "llm", None, usage or {})


RankedItem = Union[str, Tuple[str, Optional[float]]]


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Tuple[str, float, Sequence[RankedItem]]],
    k: int = DEFAULT_RRF_K,
    score_exponent: float = 0.0,
) -> List[Tuple[str, float, List[str]]]:
    """
    Merge ranked lists of identifiers with weighted reciprocal rank fusion.

    ``score(d) = sum(weight * q / (k + rank))`` over every list containing ``d``
    (ranks start at 1).  Items may be bare ids (``q = 1``) or ``(id, score)``
    pairs, where ``score`` is a 0-100 search score and
    ``q = (score / 100) ** score_exponent`` (clamped to [0, 1]); with
    ``score_exponent=0`` this is plain weighted RRF.  Score weighting keeps a
    weak fuzzy match at rank 1 from counting as much as an exact one.
    Ties keep first-seen order.

    Args:
        ranked_lists: ``(term, weight, items_in_rank_order)`` triples.
        k (int): The RRF damping constant.
        score_exponent (float): Exponent applied to normalised search scores.

    Returns:
        List[Tuple[str, float, List[str]]]: ``(id, score, terms)`` sorted by
            descending score; ``terms`` lists the matching terms, strongest first.
    """
    scores: Dict[str, float] = {}
    contributions: Dict[str, Dict[str, float]] = {}
    for term, weight, ids in ranked_lists:
        if weight <= 0:
            continue
        seen = set()
        rank = 0
        for entry in ids:
            item, raw_score = entry if isinstance(entry, tuple) else (entry, None)
            if item in seen:
                continue
            seen.add(item)
            rank += 1
            quality = 1.0
            if score_exponent and isinstance(raw_score, (int, float)):
                quality = min(max(raw_score / MAX_SEARCH_SCORE, 0.0), 1.0)
                quality **= score_exponent
            gain = weight * quality / (k + rank)
            if gain <= 0:
                continue
            scores[item] = scores.get(item, 0.0) + gain
            terms = contributions.setdefault(item, {})
            terms[term] = terms.get(term, 0.0) + gain
    order = {item: index for index, item in enumerate(scores)}
    fused = sorted(scores.items(), key=lambda pair: (-pair[1], order[pair[0]]))
    return [
        (
            item,
            score,
            [
                term
                for term, _ in sorted(
                    contributions[item].items(), key=lambda pair: -pair[1]
                )
            ],
        )
        for item, score in fused
    ]


@dataclass
class ExpandedSearchHit:
    """One fused search hit."""

    owl_class: OWLClass
    score: float
    matched_via: List[str]


@dataclass
class ExpandedSearchResult:
    """The result of :func:`search_expanded`."""

    query: str
    expansions: List[str]
    hits: List[ExpandedSearchHit]
    expansion_source: ExpansionSource
    expansion_error: Optional[str] = None
    elapsed_ms: float = 0.0
    usage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable summary (classes reduced to iri/label)."""
        return {
            "query": self.query,
            "expansions": list(self.expansions),
            "expansion_source": self.expansion_source,
            "expansion_error": self.expansion_error,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "results": [
                {
                    "iri": hit.owl_class.iri,
                    "label": hit.owl_class.label,
                    "score": hit.score,
                    "matched_via": list(hit.matched_via),
                }
                for hit in self.hits
            ],
        }


_EXPANDERS: "weakref.WeakKeyDictionary[Any, QueryExpander]" = (
    weakref.WeakKeyDictionary()
)
_EXPANDERS_LOCK = threading.Lock()


def get_expander(owner: Any) -> QueryExpander:
    """
    Return the expander (and its cache) associated with a FOLIO instance.

    Args:
        owner (Any): The FOLIO instance.

    Returns:
        QueryExpander: The shared expander for that instance.
    """
    with _EXPANDERS_LOCK:
        expander = _EXPANDERS.get(owner)
        if expander is None:
            expander = QueryExpander()
            _EXPANDERS[owner] = expander
        return expander


async def expand_query(
    folio: FOLIO,
    query: str,
    max_expansions: int = DEFAULT_MAX_EXPANSIONS,
    timeout: float = DEFAULT_EXPANSION_TIMEOUT,
) -> List[str]:
    """
    Expand a query with the FOLIO instance's LLM; never raises.

    Args:
        folio (FOLIO): The FOLIO instance (provides ``llm`` and ``llm_kwargs``).
        query (str): The user query.
        max_expansions (int): Maximum expansions to return (0-10).
        timeout (float): Hard timeout in seconds for the LLM call.

    Returns:
        List[str]: The expansions; empty when the LLM is unavailable.
    """
    return await get_expander(folio).expand(
        query,
        getattr(folio, "llm", None),
        getattr(folio, "llm_kwargs", None),
        max_expansions=max_expansions,
        timeout=timeout,
    )


def _scored_iris(
    results: Sequence[Tuple[OWLClass, Any]],
) -> List[Tuple[str, Optional[float]]]:
    return [
        (owl_class.iri, float(score) if isinstance(score, (int, float)) else None)
        for owl_class, score in results
    ]


async def _run_search(
    search: Callable[[], Sequence[Tuple[OWLClass, Any]]],
) -> List[Tuple[str, Optional[float]]]:
    return _scored_iris(await asyncio.to_thread(search))


async def search_expanded(
    folio: FOLIO,
    query: str,
    limit: int = 10,
    include_definitions: bool = DEFAULT_INCLUDE_DEFINITIONS,
    max_expansions: int = DEFAULT_MAX_EXPANSIONS,
    timeout: float = DEFAULT_EXPANSION_TIMEOUT,
    per_term_limit: int = DEFAULT_PER_TERM_LIMIT,
    rrf_k: int = DEFAULT_RRF_K,
    original_weight: float = DEFAULT_ORIGINAL_WEIGHT,
    expansion_weight: float = DEFAULT_EXPANSION_WEIGHT,
    expansion_decay: float = DEFAULT_EXPANSION_DECAY,
    definition_weight: float = DEFAULT_DEFINITION_WEIGHT,
    score_exponent: float = DEFAULT_SCORE_EXPONENT,
    anchor_score: Optional[float] = DEFAULT_ANCHOR_SCORE,
) -> ExpandedSearchResult:
    """
    Search FOLIO for a query and its LLM expansions, fused with weighted RRF.

    The original query's label search starts immediately, concurrently with the
    LLM call; expansion searches follow once the expansions arrive.  When the
    LLM is unavailable the result is the plain label search of ``query``.

    Args:
        folio (FOLIO): The FOLIO instance.
        query (str): The user query.
        limit (int): Maximum number of fused hits to return.
        include_definitions (bool): Also search definitions (lower weight).
        max_expansions (int): Maximum LLM expansions to use (0 disables the LLM).
        timeout (float): Hard timeout in seconds for the LLM call.
        per_term_limit (int): Results fetched per term before fusion.
        rrf_k (int): The RRF damping constant.
        original_weight (float): RRF weight of the original query's lists.
        expansion_weight (float): RRF weight of the first expansion's lists.
        expansion_decay (float): The i-th expansion (0-based, in LLM order) is
            weighted ``expansion_weight / (1 + expansion_decay * i)``.
        definition_weight (float): Multiplier for definition-search lists.
        score_exponent (float): Weight each hit by ``(score / 100) ** score_exponent``
            (0 = plain rank-only RRF).
        anchor_score (Optional[float]): Label hits for the original query scoring at
            least this (0-100) are kept first, so typing a concept's name still
            returns that concept at rank 1 (at most 3; None disables).

    Returns:
        ExpandedSearchResult: Fused hits, the expansions used and metadata.

    Raises:
        RuntimeError: If the search extra is not installed (as for search_by_label).
    """
    started = time.perf_counter()
    query = unicodedata.normalize("NFKC", query or "").strip()[:MAX_QUERY_CHARS]
    limit = max(int(limit), 1)
    per_term = max(int(per_term_limit), limit)
    if not query:
        return ExpandedSearchResult(query, [], [], "none")

    def searches_for(term: str) -> List[Awaitable[List[Tuple[str, Optional[float]]]]]:
        jobs = [
            _run_search(lambda: folio.search_by_label(term, limit=per_term)),
        ]
        if include_definitions:
            jobs.append(
                _run_search(lambda: folio.search_by_definition(term, limit=per_term))
            )
        return jobs

    # start the original query searches while the LLM is thinking
    original_task = asyncio.ensure_future(asyncio.gather(*searches_for(query)))
    try:
        outcome = await get_expander(folio).expand_with_outcome(
            query,
            getattr(folio, "llm", None),
            getattr(folio, "llm_kwargs", None),
            max_expansions=max_expansions,
            timeout=timeout,
        )
    except BaseException:
        original_task.cancel()
        raise
    original_lists = await original_task  # search errors propagate, like plain search

    async def expansion_lists(
        term: str,
    ) -> Optional[List[List[Tuple[str, Optional[float]]]]]:
        try:
            return list(await asyncio.gather(*searches_for(term)))
        except Exception as error:  # pylint: disable=broad-except
            LOGGER.warning("Search for expansion %r failed: %r", term, error)
            return None

    expansion_results = await asyncio.gather(
        *(expansion_lists(term) for term in outcome.expansions)
    )

    ranked: List[Tuple[str, float, Sequence[RankedItem]]] = []

    def add(
        term: str, weight: float, lists: Sequence[List[Tuple[str, Optional[float]]]]
    ) -> None:
        ranked.append((term, weight, lists[0]))
        if include_definitions and len(lists) > 1:
            ranked.append((term, weight * definition_weight, lists[1]))

    add(query, original_weight, original_lists)
    for index, (term, lists) in enumerate(zip(outcome.expansions, expansion_results)):
        if lists is not None:
            add(term, expansion_weight / (1.0 + expansion_decay * index), lists)

    fused = reciprocal_rank_fusion(ranked, k=rrf_k, score_exponent=score_exponent)
    if anchor_score is not None:
        anchors = [
            iri
            for iri, label_score in original_lists[0]
            if label_score is not None and label_score >= anchor_score
        ][:MAX_ANCHORS]
        if anchors:
            position = {iri: index for index, iri in enumerate(anchors)}
            fused.sort(key=lambda row: position.get(row[0], len(anchors)))

    hits: List[ExpandedSearchHit] = []
    for iri, score, terms in fused:
        owl_class = folio[iri]
        if owl_class is None:
            continue
        hits.append(ExpandedSearchHit(owl_class, score, terms))
        if len(hits) >= limit:
            break

    return ExpandedSearchResult(
        query=query,
        expansions=list(outcome.expansions),
        hits=hits,
        expansion_source=outcome.source,
        expansion_error=outcome.error,
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
        usage=outcome.usage,
    )
