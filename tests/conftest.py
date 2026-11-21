"""Small local ontologies for deterministic boundary tests."""

from copy import deepcopy

import pytest

import folio.graph
from folio import FOLIO
from folio.models import NSMAP


@pytest.fixture
def local_graph(monkeypatch):
    monkeypatch.setattr(folio.graph, "alea_llm_client", None)

    def load(contents=""):
        namespaces = " ".join(
            f'xmlns:{prefix}="{uri}"'
            for prefix, uri in NSMAP.items()
            if prefix is not None
        )
        document = f"<rdf:RDF {namespaces}>{contents}</rdf:RDF>"
        monkeypatch.setattr(FOLIO, "load_owl", staticmethod(lambda **kwargs: document))
        return FOLIO(use_cache=False)

    return load


@pytest.fixture
def legacy_graph_snapshot():
    """Capture legacy parsed state independently of the retained source XML."""

    def snapshot(graph):
        fields = (
            "title",
            "description",
            "iri_to_index",
            "iri_to_property_index",
            "label_to_index",
            "alt_label_to_index",
            "property_label_to_index",
            "class_edges",
            "triples",
            "_cached_triples",
            "_prefix_rank_bonus",
            "_lowercase_to_original",
        )
        state = {field: deepcopy(getattr(graph, field)) for field in fields}
        state["classes"] = [item.model_dump() for item in graph.classes]
        state["object_properties"] = [
            item.model_dump() for item in graph.object_properties
        ]
        for field in ("_label_trie", "_lowercase_label_trie"):
            trie = getattr(graph, field)
            state[field] = sorted(trie.keys()) if trie is not None else None
        return state

    return snapshot
