"""Parsing keeps optional text distinct from RDF relationships."""

import json

import pytest

from folio import FOLIO


CLASS = "https://folio.openlegalstandard.org/Rchild"
PARENT = "https://folio.openlegalstandard.org/Rparent"
MISSING = "https://folio.openlegalstandard.org/Rmissing"
PROPERTY = "https://folio.openlegalstandard.org/Rproperty"


def test_sparse_class_text_and_relationships(local_graph):
    empty = "".join(
        f"<{tag}/>"
        for tag in (
            "rdfs:comment",
            "skos:prefLabel",
            "skos:altLabel",
            "skos:hiddenLabel",
            "skos:definition",
            "skos:example",
            "skos:note",
            "skos:historyNote",
            "skos:editorialNote",
            "skos:inScheme",
            "dc:identifier",
            "dc:description",
            "dc:source",
            "v1:country",
        )
    )
    graph = local_graph(f'''
        <owl:Class rdf:about="{PARENT}"><rdfs:label>Parent</rdfs:label></owl:Class>
        <owl:Class rdf:about="{CLASS}">
            <rdfs:label>Child</rdfs:label>{empty}
            <skos:altLabel xml:lang="de"/>
            <skos:altLabel>  Alias  </skos:altLabel>
            <skos:example>Example</skos:example><skos:note>Note</skos:note>
            <rdfs:subClassOf rdf:resource="{PARENT}"/>
            <rdfs:subClassOf rdf:resource="{MISSING}"/>
            <rdfs:isDefinedBy rdf:resource="https://example.org/ontology"/>
            <rdfs:seeAlso rdf:resource="{PARENT}"/>
        </owl:Class>
        <owl:Class><rdfs:label>No identifier</rdfs:label></owl:Class>
        <owl:Class rdf:about="https://example.org/unlabeled"><rdfs:label/></owl:Class>
        <owl:Class rdf:about="http://www.w3.org/2002/07/owl#Thing"/>
    ''')
    child = graph[CLASS]
    assert child.label == "Child"
    assert child.alternative_labels == ["  Alias  "]
    assert child.examples == ["Example"]
    assert child.notes == ["Note"]
    assert child.translations == {}
    assert child.definition is None and child.comment is None
    assert child.sub_class_of == [PARENT, MISSING]
    assert child.see_also == [PARENT]
    assert child.is_defined_by == "https://example.org/ontology"
    assert graph["https://example.org/unlabeled"] is None
    assert graph.get_by_label("No identifier") == []
    assert graph["http://www.w3.org/2002/07/owl#Thing"] is not None
    assert all(isinstance(value, str) for triple in graph.triples for value in triple)


def test_sparse_property_retains_links_and_indexes(local_graph):
    graph = local_graph(f'''
        <owl:ObjectProperty rdf:about="{PROPERTY}">
            <rdfs:label>Connects</rdfs:label>
            <skos:prefLabel/><skos:altLabel/><skos:definition/><skos:example/>
            <skos:prefLabel>Links</skos:prefLabel><skos:altLabel>Related</skos:altLabel>
            <skos:example>A link</skos:example>
            <rdfs:subPropertyOf rdf:resource="{PARENT}"/>
            <rdfs:domain rdf:resource="{CLASS}"/>
            <rdfs:range rdf:resource="{PARENT}"/>
            <owl:inverseOf rdf:resource="{MISSING}"/>
        </owl:ObjectProperty>
        <owl:ObjectProperty><rdfs:label>No identifier</rdfs:label></owl:ObjectProperty>
        <owl:ObjectProperty rdf:about="https://example.org/unlabeled"><rdfs:label/></owl:ObjectProperty>
    ''')
    prop = graph.get_property(PROPERTY)
    assert prop.alternative_labels == ["Related"]
    assert prop.examples == ["A link"]
    assert prop.definition is None
    assert prop.domain == [CLASS] and prop.range == [PARENT]
    assert prop.sub_property_of == [PARENT] and prop.inverse_of == MISSING
    assert graph.get_properties_by_label("Connects") == [prop]
    assert graph.get_properties_by_label("Links") == [prop]
    assert (CLASS, "Connects", PARENT) in graph.triples
    assert graph.get_property("https://example.org/unlabeled") is None
    assert all(isinstance(value, str) for triple in graph.triples for value in triple)


@pytest.mark.parametrize("known_parent", [True, False])
def test_llm_formatting_omits_unresolved_parents(local_graph, known_parent):
    graph = local_graph(f'''
        <owl:Class rdf:about="{PARENT}">
            <rdfs:label>Parent</rdfs:label><skos:prefLabel>Preferred parent</skos:prefLabel>
        </owl:Class>
        <owl:Class rdf:about="{CLASS}">
            <rdfs:label>Child</rdfs:label>
            <rdfs:subClassOf rdf:resource="{MISSING}"/>
            {f'<rdfs:subClassOf rdf:resource="{PARENT}"/>' if known_parent else ""}
        </owl:Class>
    ''')
    child = graph[CLASS]
    data = json.loads(graph.format_classes_for_llm([child]))
    assert data["iri"] == CLASS
    assert data.get("parents", []) == (["Preferred parent"] if known_parent else [])
    assert MISSING in child.sub_class_of


def test_http_loader_rejects_missing_url():
    with pytest.raises(TypeError):
        FOLIO.load_owl_http(None)
