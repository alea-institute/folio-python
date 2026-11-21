"""Probe an installed wheel in a separately prepared core-only environment."""

import os
import subprocess

import pytest


CORE_PROBE = '''
import asyncio
import importlib.util
from importlib.metadata import PackageNotFoundError, version

for module, distribution in (
    ("rapidfuzz", "rapidfuzz"),
    ("marisa_trie", "marisa-trie"),
    ("alea_llm_client", "alea-llm-client"),
    ("kaos_nlp_core", "kaos-nlp-core"),
):
    assert importlib.util.find_spec(module) is None, module
    try:
        version(distribution)
    except PackageNotFoundError:
        pass
    else:
        raise AssertionError(f"Optional distribution installed: {distribution}")

from folio import FOLIO
import folio.graph

assert all(module is None for module in (
    folio.graph.rapidfuzz, folio.graph.marisa_trie, folio.graph.alea_llm_client
))
iri = "https://folio.openlegalstandard.org/Rcontract"
document = f"""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:skos="http://www.w3.org/2004/02/skos/core#">
    <owl:Class rdf:about="{iri}">
        <rdfs:label>Contract</rdfs:label><skos:altLabel>Agreement</skos:altLabel>
    </owl:Class>
</rdf:RDF>"""
FOLIO.load_owl = staticmethod(lambda **kwargs: document)
graph = FOLIO(use_cache=False)
assert len(graph) == 1
assert graph._label_trie is None and graph._lowercase_label_trie is None
assert [item.iri for item in graph.search_by_prefix("CON")] == [iri]
assert [item.iri for item in graph.search_by_prefix("Agr", case_sensitive=True)] == [iri]
assert [item.iri for item in graph.query(label="Contract", match_mode="exact")] == [iri]
assert [item.iri for item in graph.query(label="tract", match_mode="substring")] == [iri]
for search in (graph.search_by_label, graph.search_by_definition):
    try:
        search("contract")
    except RuntimeError as error:
        assert "search extra must be installed" in str(error)
    else:
        raise AssertionError("Fuzzy search unexpectedly succeeded")

async def check_llm_errors():
    for result in (
        graph.search_by_llm("contract", graph.classes),
        graph.parallel_search_by_llm("contract", [graph.classes]),
    ):
        try:
            await result
        except RuntimeError as error:
            assert "search extra must be installed" in str(error)
        else:
            raise AssertionError("LLM search unexpectedly succeeded")

asyncio.run(check_llm_errors())
print("core-only wheel probe passed")
'''


def test_core_only_installed_wheel(tmp_path):
    python = os.environ.get("FOLIO_CORE_PYTHON")
    if not python:
        pytest.skip("Set FOLIO_CORE_PYTHON to a separately installed core-only Python")
    # -I and a different cwd prevent importing this checkout or its development packages.
    result = subprocess.run(
        [python, "-I", "-c", CORE_PROBE],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "core-only wheel probe passed" in result.stdout


PREFIX_RANKING_PROBE = '''
import importlib.util
from folio import FOLIO
from folio.models import NSMAP

assert importlib.util.find_spec("marisa_trie") is None
assert importlib.util.find_spec("rapidfuzz") is None
assert importlib.util.find_spec("alea_llm_client") is None
namespaces = " ".join(f'xmlns:{prefix}="{uri}"' for prefix, uri in NSMAP.items() if prefix)
base = "https://folio.openlegalstandard.org/"
document = f"""<rdf:RDF {namespaces}>
    <owl:Class rdf:about="{base}alias">
        <rdfs:label>Other</rdfs:label><skos:altLabel>Match</skos:altLabel>
    </owl:Class>
    <owl:Class rdf:about="{base}deep">
        <rdfs:label>Match extension</rdfs:label>
        <rdfs:subClassOf rdf:resource="{base}shallow"/>
    </owl:Class>
    <owl:Class rdf:about="{base}shallow">
        <rdfs:label>Match extension</rdfs:label>
    </owl:Class>
    <owl:Class rdf:about="{base}exact">
        <rdfs:label>Match</rdfs:label>
    </owl:Class>
</rdf:RDF>"""
FOLIO.load_owl = staticmethod(lambda **kwargs: document)
graph = FOLIO(use_cache=False)
assert graph._label_trie is None and graph._lowercase_label_trie is None
for case_sensitive in (True, False):
    prefix = "Match" if case_sensitive else "MATCH"
    for _ in range(2):
        assert [item.iri for item in graph.search_by_prefix(prefix, case_sensitive)] == [
            base + name for name in ("exact", "shallow", "deep", "alias")
        ]
print("core-only prefix ranking passed")
'''


def test_prefix_ranking_in_core_only_installed_wheel(tmp_path):
    python = os.environ.get("FOLIO_CORE_PYTHON")
    if not python:
        pytest.skip("Set FOLIO_CORE_PYTHON to a separately installed core-only Python")
    result = subprocess.run(
        [python, "-I", "-c", PREFIX_RANKING_PROBE],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "core-only prefix ranking passed" in result.stdout


METADATA_PROBE = """
import importlib.util
from dataclasses import FrozenInstanceError
from folio import FOLIO, NSMAP, OWLNode

for module in ("rapidfuzz", "marisa_trie", "alea_llm_client", "kaos_nlp_core"):
    assert importlib.util.find_spec(module) is None
namespaces = " ".join(f'xmlns:{prefix}="{uri}"' for prefix, uri in NSMAP.items() if prefix)
kinds = (
    ("owl:DatatypeProperty", "datatype_properties"),
    ("owl:AnnotationProperty", "annotation_properties"),
    ("owl:NamedIndividual", "named_individuals"),
    ("rdf:Description", "rdf_descriptions"),
)
body = "".join(
    f'<{tag} rdf:about="https://example.org/{name}"><rdfs:label>Metadata</rdfs:label></{tag}>'
    for tag, name in kinds
)
FOLIO.load_owl = staticmethod(lambda **kwargs: f'<rdf:RDF {namespaces}>{body}</rdf:RDF>')
graph = FOLIO(use_cache=False)
for tag, name in kinds:
    records = getattr(graph, name)
    assert isinstance(records, tuple) and len(records) == 1
    record = records[0]
    assert isinstance(record, OWLNode)
    assert record.iri == f"https://example.org/{name}"
    assert record.children[0].text == "Metadata"
    try:
        record.children[0].text = "changed"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Mutable metadata")
assert not graph.classes and not graph.object_properties and not graph.triples
print("core-only metadata probe passed")
"""


def test_metadata_in_core_only_installed_wheel(tmp_path):
    python = os.environ.get("FOLIO_CORE_PYTHON")
    if not python:
        pytest.skip("Set FOLIO_CORE_PYTHON to a separately installed core-only Python")
    result = subprocess.run(
        [python, "-I", "-c", METADATA_PROBE],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "core-only metadata probe passed" in result.stdout
