"""Deterministic checks of the ontology model's public export formats."""

import json

import lxml.etree
import pytest

from folio import OWLClass


IRI = "https://folio.openlegalstandard.org/Rexample"
PARENT = "https://folio.openlegalstandard.org/Rparent"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
XML = "http://www.w3.org/XML/1998/namespace"


@pytest.mark.parametrize(
    ("alternatives", "translations", "expected"),
    [
        (
            ["Road", "Street"],
            {"fr": "Rue", "de": "Straße"},
            [
                "Road",
                "Street",
                {"@value": "Straße", "@language": "de"},
                {"@value": "Rue", "@language": "fr"},
            ],
        ),
        (
            [],
            {"fr": "Rue", "de": "Straße"},
            [
                {"@value": "Straße", "@language": "de"},
                {"@value": "Rue", "@language": "fr"},
            ],
        ),
        (["Road", "Street"], {}, ["Road", "Street"]),
        ([], {}, None),
    ],
    ids=["aliases-and-translations", "translations-only", "aliases-only", "absent"],
)
def test_jsonld_preserves_all_alternative_labels(alternatives, translations, expected):
    owl_class = OWLClass(
        iri=IRI, alternative_labels=alternatives, translations=translations
    )

    exported = owl_class.to_jsonld()

    if expected is None:
        assert "skos:altLabel" not in exported
    else:
        assert exported["skos:altLabel"] == expected
    assert exported["rdfs:label"] is None
    assert owl_class.alternative_labels == alternatives
    assert owl_class.translations == translations


@pytest.fixture
def populated_class():
    return OWLClass(
        iri=IRI,
        label="Road & street",
        sub_class_of=[PARENT],
        parent_class_of=["https://folio.openlegalstandard.org/Rchild"],
        is_defined_by="https://example.org/ontology",
        see_also=["https://example.org/related", "Related text"],
        comment="A comment",
        deprecated=True,
        preferred_label="Road",
        alternative_labels=["Street"],
        translations={"fr": "Rue", "de": "Straße"},
        hidden_label="ROAD",
        definition="A route for travel <on land>.",
        examples=["Main Street", "Elm Street"],
        notes=["Note one", "Note two"],
        history_note="Historical note",
        editorial_note="Editorial note",
        in_scheme="https://example.org/scheme",
        identifier="road-1",
        description="A description",
        source="A source",
        country="US",
    )


def test_json_round_trip_preserves_populated_fields(populated_class):
    encoded = populated_class.to_json()

    assert json.loads(encoded)["translations"] == {"fr": "Rue", "de": "Straße"}
    assert OWLClass.from_json(encoded) == populated_class


def test_json_round_trip_preserves_absent_fields():
    owl_class = OWLClass(iri=IRI)

    restored = OWLClass.from_json(owl_class.to_json())

    assert restored == owl_class
    assert restored.label is None
    assert restored.alternative_labels == []
    assert restored.translations == {}
    assert restored.deprecated is False


def test_jsonld_preserves_populated_relationships_and_annotations(populated_class):
    exported = populated_class.to_jsonld()

    assert exported["@id"] == IRI
    assert exported["@type"] == "owl:Class"
    assert exported["rdfs:label"] == "Road & street"
    assert exported["rdfs:subClassOf"] == [{"@id": PARENT}]
    assert exported["rdfs:isDefinedBy"] == "https://example.org/ontology"
    assert exported["rdfs:seeAlso"] == [
        {"@id": "https://example.org/related"},
        "Related text",
    ]
    expected_annotations = {
        "rdfs:comment": "A comment",
        "owl:deprecated": True,
        "skos:prefLabel": "Road",
        "skos:hiddenLabel": "ROAD",
        "skos:definition": "A route for travel <on land>.",
        "skos:example": ["Main Street", "Elm Street"],
        "skos:note": ["Note one", "Note two"],
        "skos:historyNote": "Historical note",
        "skos:editorialNote": "Editorial note",
        "skos:inScheme": "https://example.org/scheme",
        "dc:identifier": "road-1",
        "dc:description": "A description",
        "dc:source": "A source",
        "v1:country": "US",
    }
    for name, value in expected_annotations.items():
        assert exported[name] == value


def test_jsonld_omits_absent_annotations():
    exported = OWLClass(iri=IRI).to_jsonld()

    assert set(exported) == {"@context", "@id", "@type", "rdfs:label"}


def test_xml_preserves_namespaces_values_and_relationships(populated_class):
    root = lxml.etree.fromstring(populated_class.to_owl_xml().encode("utf-8"))

    assert root.tag == f"{{{OWL}}}Class"
    assert root.get(f"{{{RDF}}}about") == IRI
    assert root.findtext(f"{{{RDFS}}}label") == "Road & street"
    assert root.find(f"{{{RDFS}}}subClassOf").get(f"{{{RDF}}}resource") == PARENT
    assert root.find(f"{{{RDFS}}}isDefinedBy").get(f"{{{RDF}}}resource") == (
        "https://example.org/ontology"
    )
    related = root.findall(f"{{{RDFS}}}seeAlso")
    assert [(node.get(f"{{{RDF}}}resource"), node.text) for node in related] == [
        ("https://example.org/related", None),
        (None, "Related text"),
    ]
    aliases = root.findall(f"{{{SKOS}}}altLabel")
    assert [(node.get(f"{{{XML}}}lang"), node.text) for node in aliases] == [
        (None, "Street"),
        ("de", "Straße"),
        ("fr", "Rue"),
    ]
    assert root.findtext(f"{{{SKOS}}}hiddenLabel") == "ROAD"
    assert root.findtext(f"{{{SKOS}}}prefLabel") == "Road"
    assert root.findtext(f"{{{SKOS}}}definition") == "A route for travel <on land>."
    assert [node.text for node in root.findall(f"{{{SKOS}}}example")] == [
        "Main Street",
        "Elm Street",
    ]


def test_xml_omits_absent_optional_annotations():
    root = OWLClass(iri=IRI, label="Road").to_owl_element()

    assert isinstance(root, lxml.etree._Element)
    assert root.get(f"{{{RDF}}}about") == IRI
    assert [(child.tag, child.text) for child in root] == [(f"{{{RDFS}}}label", "Road")]
