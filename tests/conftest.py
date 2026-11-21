"""Local ontology fixtures and opt-in sustained cache-pressure measurements."""

import pytest

import folio.graph
from folio import FOLIO
from folio.models import NSMAP

pytest_plugins = ["pytester"]


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


def pytest_addoption(parser):
    parser.addoption(
        "--run-cache-pressure",
        action="store_true",
        default=False,
        help="run sustained cache-pressure benchmarks (at least three minutes)",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-cache-pressure"):
        skip = pytest.mark.skip(reason="requires --run-cache-pressure")
        for item in items:
            if item.get_closest_marker("cache_pressure"):
                item.add_marker(skip)
