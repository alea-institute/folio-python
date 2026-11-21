"""Metadata parsing preserves legacy graph contents and exposes detached records."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import lxml.etree
import pytest

import folio
from folio import FOLIO, NSMAP, OWLClass, OWLObjectProperty
from folio.graph import LOGGER


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
NODE_KINDS = (
    ("owl:DatatypeProperty", "datatype_properties"),
    ("owl:AnnotationProperty", "annotation_properties"),
    ("owl:NamedIndividual", "named_individuals"),
    ("rdf:Description", "rdf_descriptions"),
)


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


@pytest.mark.parametrize("tag,accessor", NODE_KINDS)
def test_metadata_records_preserve_subjects_and_literals(local_graph, tag, accessor):
    graph = local_graph(f'''
        <{tag} rdf:about="{BASE}shared">
            <skos:definition xml:lang="en">First definition</skos:definition>
            <skos:definition xml:lang="fr">Deuxième définition</skos:definition>
            <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
            <rdf:value rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">42</rdf:value>
        </{tag}>
        <{tag} rdf:about="{BASE}shared"/>
        <{tag} rdf:nodeID="blank"/>
    ''')
    records = getattr(graph, accessor)
    assert isinstance(records, tuple)
    assert len(records) == 3
    assert all(isinstance(record, folio.OWLNode) for record in records)
    assert [record.iri for record in records] == [
        BASE + "shared",
        BASE + "shared",
        None,
    ]
    assert records[1].children == ()
    assert records[2].attributes == ((FOLIO.get_ns_tag("rdf", "nodeID"), "blank"),)
    first = records[0]
    namespace, name = tag.split(":")
    assert first.tag == FOLIO.get_ns_tag(namespace, name)
    assert [child.text for child in first.children] == [
        "First definition",
        "Deuxième définition",
        None,
        "42",
    ]
    assert [
        dict(child.attributes).get(FOLIO.get_ns_tag("xml", "lang"))
        for child in first.children[:2]
    ] == ["en", "fr"]
    assert first.children[2].attributes == (
        (FOLIO.get_ns_tag("rdf", "resource"), NSMAP["xsd"] + "string"),
    )
    assert first.children[3].attributes == (
        (FOLIO.get_ns_tag("rdf", "datatype"), NSMAP["xsd"] + "integer"),
    )
    assert graph.classes == [] and graph.object_properties == []
    assert graph.triples == []


def test_nested_restrictions_and_cross_kind_subjects(local_graph):
    graph = local_graph(
        METADATA_NODES
        + f'''
        <owl:NamedIndividual rdf:about="{BASE}property">
            <rdf:type><owl:Restriction>
                <owl:onProperty rdf:resource="{BASE}property"/>
                <owl:someValuesFrom><owl:Class rdf:about="{BASE}nested"/></owl:someValuesFrom>
            </owl:Restriction></rdf:type>
            <rdfs:seeAlso><rdf:Description rdf:about="{BASE}nested"/></rdfs:seeAlso>
        </owl:NamedIndividual>
    '''
    )
    record = graph.named_individuals[1]
    restriction = record.children[0].children[0]
    assert restriction.tag == FOLIO.get_ns_tag("owl", "Restriction")
    assert restriction.children[0].attributes == (
        (FOLIO.get_ns_tag("rdf", "resource"), BASE + "property"),
    )
    assert restriction.children[1].children[0].iri == BASE + "nested"
    assert record.iri == graph.annotation_properties[0].iri
    assert len(graph.rdf_descriptions) == 1
    assert graph.classes == []


def test_mixed_content_skips_processing_instructions_without_losing_text(local_graph):
    graph = local_graph(
        """<rdf:Description>start<?a x?> middle<?b x?> end<rdf:value>before<?c x?> after<rdfs:label>label</rdfs:label> tail<?d x?> last</rdf:value> suffix<?e x?> final</rdf:Description>"""
    )
    source = graph.tree[0]
    original = lxml.etree.tostring(source)
    record = graph.rdf_descriptions[0]
    assert record.text == "start middle end"
    assert len(record.children) == 1
    value = record.children[0]
    assert value.text == "before after"
    assert value.tail == " suffix final"
    assert len(value.children) == 1
    assert value.children[0].text == "label"
    assert value.children[0].tail == " tail last"
    assert lxml.etree.tostring(source) == original
    assert len(source.xpath(".//processing-instruction()")) == 5


def test_direct_capture_preserves_source_xml(local_graph):
    namespaces = " ".join(
        f'xmlns:{prefix}="{uri}"' for prefix, uri in NSMAP.items() if prefix
    )
    source = lxml.etree.fromstring(
        f'''<rdf:Description {namespaces} rdf:about="{BASE}source">before<?keep one?> middle<skos:definition xml:lang="en">First<?keep two?> definition</skos:definition> between<skos:definition xml:lang="fr">Deuxième</skos:definition> after<?keep three?> end</rdf:Description>'''.encode()
    )
    original = lxml.etree.tostring(source)
    graph = local_graph()
    assert graph.parse_node(source) is None
    record = graph.rdf_descriptions[0]
    assert record.iri == BASE + "source"
    assert record.text == "before middle"
    assert [child.text for child in record.children] == ["First definition", "Deuxième"]
    assert [child.tail for child in record.children] == [" between", " after end"]
    assert lxml.etree.tostring(source) == original


@pytest.mark.parametrize("tag,accessor", NODE_KINDS)
def test_read_only_detached_snapshots(local_graph, tag, accessor):
    graph = local_graph(
        f'<{tag} rdf:about="{BASE}before"><rdfs:label>Before</rdfs:label></{tag}>'
    )
    records = getattr(graph, accessor)
    record = records[0]
    with pytest.raises(AttributeError):
        setattr(graph, accessor, ())
    with pytest.raises(FrozenInstanceError):
        record.text = "changed"
    with pytest.raises(FrozenInstanceError):
        record.children[0].text = "changed"
    with pytest.raises(TypeError):
        record.children[0] = record
    with pytest.raises(TypeError):
        record.attributes[0] = ("changed", "changed")
    with pytest.raises(TypeError):
        record.attributes[0][1] = "changed"
    with pytest.raises(AttributeError):
        records.append(record)
    source = graph.tree[0]
    source.set(FOLIO.get_ns_tag("rdf", "about"), BASE + "after")
    source[0].text = "After"
    source.append(lxml.etree.Element("extra"))
    assert record.iri == BASE + "before"
    assert record.children[0].text == "Before"
    assert len(record.children) == 1


@pytest.mark.parametrize("operation", ["parse_owl", "refresh"])
def test_metadata_lifecycle_replaces_snapshots(local_graph, operation):
    graph = local_graph(METADATA_NODES)
    previous = {name: getattr(graph, name) for _, name in NODE_KINDS}
    replacement = local_graph(
        "".join(f'<{tag} rdf:about="{BASE}replacement"/>' for tag, _ in NODE_KINDS)
    )
    if operation == "parse_owl":
        graph.parse_owl(lxml.etree.tostring(replacement.tree).decode())
    else:
        graph.refresh()
    for _, name in NODE_KINDS:
        records = getattr(graph, name)
        assert len(records) == 1
        assert records[0].iri == BASE + "replacement"
        assert len(previous[name]) == 1
        assert previous[name][0].iri != records[0].iri
    empty = local_graph()
    if operation == "parse_owl":
        graph.parse_owl(lxml.etree.tostring(empty.tree).decode())
    else:
        graph.refresh()
    assert all(getattr(graph, name) == () for _, name in NODE_KINDS)
    assert all(len(getattr(replacement, name)) == 1 for _, name in NODE_KINDS)


@pytest.mark.parametrize("operation", ["parse_owl", "refresh"])
def test_malformed_xml_retains_metadata(local_graph, monkeypatch, operation):
    graph = local_graph(METADATA_NODES)
    previous = {name: getattr(graph, name) for _, name in NODE_KINDS}
    monkeypatch.setattr(FOLIO, "load_owl", staticmethod(lambda **kwargs: "<broken>"))
    with pytest.raises(lxml.etree.XMLSyntaxError):
        if operation == "parse_owl":
            graph.parse_owl("<broken>")
        else:
            graph.refresh()
    assert all(getattr(graph, name) is previous[name] for _, name in NODE_KINDS)


@pytest.mark.parametrize("tag,accessor", NODE_KINDS)
def test_direct_dispatch_appends_without_changing_legacy_state(
    local_graph, legacy_graph_snapshot, tag, accessor
):
    graph = local_graph(LEGACY_NODES)
    previous = getattr(graph, accessor)
    assert previous == ()
    state = legacy_graph_snapshot(graph)
    source = local_graph(f'<{tag} rdf:about="{BASE}direct"/>').tree[0]
    assert graph.parse_node(source) is None
    assert len(getattr(graph, accessor)) == 1
    assert getattr(graph, accessor)[0].iri == BASE + "direct"
    assert previous == ()
    assert legacy_graph_snapshot(graph) == state


def test_unknown_root_type_keeps_debug_logging(local_graph, caplog):
    with caplog.at_level("DEBUG", logger=LOGGER.name):
        graph = local_graph("<owl:Unrecognized/>")
    assert (
        "Unknown node type: {http://www.w3.org/2002/07/owl#}Unrecognized" in caplog.text
    )
    assert all(getattr(graph, name) == () for _, name in NODE_KINDS)


def test_readme_metadata_example(local_graph, capsys):
    local_graph(METADATA_NODES)
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text()
    section = readme.split("## Read-only ontology metadata\n", 1)[1].split("\n## ", 1)[
        0
    ]
    code = section.split("```python\n", 1)[1].split("```", 1)[0]
    namespace = {}
    exec(compile(code, "README.md", "exec"), namespace)
    assert capsys.readouterr().out == BASE + "property ['Annotation']\n"
    assert isinstance(namespace["declaration"], folio.OWLNode)
