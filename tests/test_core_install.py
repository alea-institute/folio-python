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
