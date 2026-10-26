"""Small local ontologies for deterministic boundary tests."""

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
