"""Metadata parsing preserves legacy graph contents and exposes detached records."""

from folio import OWLClass, OWLObjectProperty


BASE = "https://folio.openlegalstandard.org/"
LEGACY_NODES = f"""
<owl:Ontology rdf:about="{BASE}">
    <dc:title>Fixture ontology</dc:title><dc:description>Parser fixture</dc:description>
</owl:Ontology>
<owl:Class rdf:about="{BASE}parent"><rdfs:label>Parent</rdfs:label></owl:Class>
<owl:Class rdf:about="{BASE}child">
    <rdfs:label>Child</rdfs:label><skos:altLabel>Alias</skos:altLabel>
    <rdfs:subClassOf rdf:resource="{BASE}parent"/>
</owl:Class>
<owl:ObjectProperty rdf:about="{BASE}property">
    <rdfs:label>Connects</rdfs:label>
    <rdfs:domain rdf:resource="{BASE}child"/><rdfs:range rdf:resource="{BASE}parent"/>
</owl:ObjectProperty>
"""
METADATA_NODES = f"""
<owl:DatatypeProperty rdf:about="{BASE}datatype"/>
<owl:AnnotationProperty rdf:about="{BASE}property"><rdfs:label>Annotation</rdfs:label></owl:AnnotationProperty>
<owl:NamedIndividual rdf:about="{BASE}individual"><rdf:type rdf:resource="{BASE}child"/></owl:NamedIndividual>
<rdf:Description rdf:about="{BASE}child"><rdfs:label>Different label</rdfs:label></rdf:Description>
"""


def test_legacy_contents_with_metadata(local_graph, legacy_graph_snapshot):
    control = local_graph(LEGACY_NODES)
    graph = local_graph(LEGACY_NODES + METADATA_NODES)
    assert len(graph.classes) == 2
    assert len(graph.object_properties) == 1
    assert graph.classes == [
        OWLClass(iri=BASE + "parent", label="Parent", parent_class_of=[BASE + "child"]),
        OWLClass(
            iri=BASE + "child",
            label="Child",
            alternative_labels=["Alias"],
            sub_class_of=[BASE + "parent"],
        ),
    ]
    assert graph.object_properties == [
        OWLObjectProperty(
            iri=BASE + "property",
            label="Connects",
            domain=[BASE + "child"],
            range=[BASE + "parent"],
        )
    ]
    assert graph.title == "Fixture ontology"
    assert graph.description == "Parser fixture"
    assert graph.iri_to_index == {BASE + "parent": 0, BASE + "child": 1}
    assert graph.iri_to_property_index == {BASE + "property": 0}
    assert graph.label_to_index == {"Parent": [0], "Child": [1]}
    assert graph.alt_label_to_index == {"Alias": [1]}
    assert graph.property_label_to_index == {"Connects": [0]}
    assert graph.class_edges == {BASE + "parent": [BASE + "child"]}
    assert graph.triples == [
        (BASE + "parent", "rdfs:label", "Parent"),
        (BASE + "child", "rdfs:label", "Child"),
        (BASE + "child", "skos:altLabel", "Alias"),
        (BASE + "child", "rdfs:subClassOf", BASE + "parent"),
        (BASE + "property", "rdfs:label", "Connects"),
        (BASE + "property", "rdfs:domain", BASE + "child"),
        (BASE + "property", "rdfs:range", BASE + "parent"),
    ]
    assert graph._cached_triples == tuple(graph.triples)
    assert legacy_graph_snapshot(graph) == legacy_graph_snapshot(control)
