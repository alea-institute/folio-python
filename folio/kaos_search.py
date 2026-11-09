"""
Optional kaos-nlp-core backed search indices for FOLIO label and definition search.

When the optional ``kaos`` extra is installed (``kaos-nlp-core``, Python >= 3.13),
``FOLIO.search_by_label`` and ``FOLIO.search_by_definition`` use the BM25
inverted indices defined here instead of a RapidFuzz scan over every string:

* **Labels** are indexed as character trigrams of each lowercased word
  (``"#tr", "tru", "rus", "ust", "st#"``), scored with BM25.  Trigrams make the
  index tolerant of typos ("copyrite"), word order and partial words, while BM25
  rewards rare, specific matches.  A label whose normalized text equals the
  normalized query is always ranked first.
* **Definitions** are indexed as lowercased words and scored with BM25.

Both indices are built lazily, once per ``FOLIO`` instance, under a lock, and
are dropped by ``FOLIO.refresh()``.  Queries run in Rust and release the GIL.

Scores are on the same 0-100 scale as the RapidFuzz path (higher is better and
results are returned in descending score order).  A result's score is its BM25
score relative to the best hit, multiplied by the best hit's lexical overlap
with the query (trigram Dice coefficient for labels, query-word coverage for
definitions); exact label matches score 100.

Set the environment variable ``FOLIO_SEARCH_BACKEND=rapidfuzz`` to force the
RapidFuzz implementation even when kaos-nlp-core is installed.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import re
import threading
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from folio.logger import get_logger

LOGGER = get_logger(__name__)

# environment variable used to force the RapidFuzz backend
SEARCH_BACKEND_ENV = "FOLIO_SEARCH_BACKEND"

# number of index hits fetched per requested result; label strings map to one or
# more classes and several strings can map to the same class, so over-fetch.
_OVERFETCH = 5
_MIN_FETCH = 50

_TOKEN_SPLIT = re.compile(r"[\W_]+", re.UNICODE)

_inverted_index: Optional[Any] = None
try:
    if importlib.util.find_spec("kaos_nlp_core") is not None:
        _inverted_index = importlib.import_module(
            "kaos_nlp_core.structures"
        ).InvertedIndex
except Exception as error:  # pylint: disable=broad-except
    LOGGER.warning("Disabling kaos-nlp-core search backend: %s", error)
    _inverted_index = None

KAOS_AVAILABLE: bool = _inverted_index is not None


def kaos_enabled() -> bool:
    """Return True when the kaos-nlp-core backend is installed and not disabled."""
    if not KAOS_AVAILABLE:
        return False
    backend = os.environ.get(SEARCH_BACKEND_ENV, "auto").strip().lower()
    return backend not in {"rapidfuzz", "legacy"}


def tokenize_words(text: str) -> List[str]:
    """Lowercase ``text`` and split it on any run of non-word characters."""
    return [token for token in _TOKEN_SPLIT.split(text.casefold()) if token]


def tokenize_trigrams(text: str) -> List[str]:
    """Return the boundary-padded character trigrams of every word in ``text``."""
    trigrams: List[str] = []
    for word in tokenize_words(text):
        padded = f"#{word}#"
        trigrams.extend(padded[i : i + 3] for i in range(len(padded) - 2))
    return trigrams


def _dice(left: Iterable[str], right: Iterable[str]) -> float:
    """Dice coefficient of two token sets."""
    left_set, right_set = set(left), set(right)
    if not left_set or not right_set:
        return 0.0
    return 2.0 * len(left_set & right_set) / (len(left_set) + len(right_set))


def _build(texts: Sequence[str], tokenize: Callable[[str], List[str]]) -> Any:
    """Build a kaos-nlp-core inverted index with one document per text.

    Documents are added one at a time rather than with ``build_batch`` so the
    tokenized corpus is never materialized in Python (~14 MB vs ~200 MB peak
    for the FOLIO label index).
    """
    if _inverted_index is None:
        raise RuntimeError("kaos-nlp-core is not installed")
    index = _inverted_index()
    for doc_id, text in enumerate(texts):
        index.add_document(doc_id, tokenize(text))
    return index


def _scale(
    hits: Sequence[Tuple[int, float]], quality: float
) -> List[Tuple[int, float]]:
    """Map raw BM25 scores to 0-100: relative to the best hit, times its quality."""
    if not hits:
        return []
    top = hits[0][1]
    if top <= 0:
        return [(doc_id, 0.0) for doc_id, _ in hits]
    return [(doc_id, round(100.0 * quality * score / top, 2)) for doc_id, score in hits]


class LabelIndex:
    """Trigram BM25 index over a fixed sequence of label strings."""

    def __init__(self, labels: Sequence[str]) -> None:
        self.labels: Tuple[str, ...] = tuple(labels)
        self._index = _build(self.labels, tokenize_trigrams)
        self._normalized: Dict[str, List[int]] = {}
        for doc_id, label in enumerate(self.labels):
            key = " ".join(tokenize_words(label))
            if key:
                self._normalized.setdefault(key, []).append(doc_id)

    def search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """Return up to ``top_k`` ``(label, score)`` pairs, best first."""
        words = tokenize_words(query)
        if not words or top_k <= 0:
            return []
        query_trigrams = tokenize_trigrams(query)
        exact = self._normalized.get(" ".join(words), [])
        exact_set = set(exact)
        ranked = [
            (hit.doc_id, float(hit.score))
            for hit in self._index.query_bm25(query_trigrams, top_k=top_k)
            if hit.doc_id not in exact_set
        ]
        quality = (
            _dice(query_trigrams, tokenize_trigrams(self.labels[ranked[0][0]]))
            if ranked
            else 0.0
        )
        scored = [(doc_id, 100.0) for doc_id in exact] + _scale(ranked, quality)
        return [(self.labels[doc_id], score) for doc_id, score in scored[:top_k]]


class DefinitionIndex:
    """Word BM25 index over class definitions."""

    def __init__(self, definitions: Sequence[Tuple[int, str]]) -> None:
        self.class_indices: Tuple[int, ...] = tuple(index for index, _ in definitions)
        self._texts: Tuple[str, ...] = tuple(text for _, text in definitions)
        self._index = _build(self._texts, tokenize_words)

    def search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Return up to ``top_k`` ``(class index, score)`` pairs, best first."""
        words = tokenize_words(query)
        if not words or top_k <= 0 or not self._texts:
            return []
        ranked = [
            (hit.doc_id, float(hit.score))
            for hit in self._index.query_bm25(words, top_k=top_k)
        ]
        quality = 0.0
        if ranked:
            query_words = set(words)
            top_words = set(tokenize_words(self._texts[ranked[0][0]]))
            quality = len(query_words & top_words) / len(query_words)
        return [
            (self.class_indices[doc_id], score)
            for doc_id, score in _scale(ranked, quality)
        ]


class KaosSearchIndices:
    """Lazily built, thread-safe holder for one FOLIO instance's search indices."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._labels: Dict[bool, LabelIndex] = {}
        self._definitions: Optional[DefinitionIndex] = None

    def clear(self) -> None:
        """Drop all built indices (e.g. after the ontology is reloaded)."""
        with self._lock:
            self._labels = {}
            self._definitions = None

    def labels(
        self, include_alt_labels: bool, source: Callable[[], Sequence[str]]
    ) -> LabelIndex:
        """Return the label index, building it from ``source()`` on first use."""
        index = self._labels.get(include_alt_labels)
        if index is None:
            with self._lock:
                index = self._labels.get(include_alt_labels)
                if index is None:
                    index = LabelIndex(source())
                    self._labels[include_alt_labels] = index
        return index

    def definitions(
        self, source: Callable[[], Sequence[Tuple[int, str]]]
    ) -> DefinitionIndex:
        """Return the definition index, building it from ``source()`` on first use."""
        index = self._definitions
        if index is None:
            with self._lock:
                index = self._definitions
                if index is None:
                    index = DefinitionIndex(source())
                    self._definitions = index
        return index


def overfetch(limit: int) -> int:
    """Number of index hits to request for ``limit`` deduplicated results."""
    return max(limit * _OVERFETCH, _MIN_FETCH)
