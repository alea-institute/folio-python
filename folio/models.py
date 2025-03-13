"""
This module contains the OWLClass model and related pydantic models for the FOLIO package.
"""

# pylint: disable=fixme,no-member,unsupported-assignment-operation,too-many-lines,too-many-public-methods

# imports
from typing import Dict, List, Optional, Any

# packages
import lxml.etree
from pydantic import BaseModel, Field

# Default values for configuration
NSMAP = {
    None: "https://folio.openlegalstandard.org/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "v1": "http://www.loc.gov/mads/rdf/v1#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "folio": "https://folio.openlegalstandard.org/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xml": "http://www.w3.org/XML/1998/namespace",
}


class OWLClass(BaseModel):
    """
    OWLClass model for the FOLIO package, which represents an OWL class in the FOLIO
    ontology/taxonomy style.

    TODO: think about future-proofing for next-gen roadmap.
    """

    iri: str = Field(..., description="{http://www.w3.org/2002/07/owl#}Class")
    label: Optional[str] = Field(
        None, description="{http://www.w3.org/2000/01/rdf-schema#}label"
    )
    sub_class_of: List[str] = Field(
        default_factory=list,
        description="{http://www.w3.org/2000/01/rdf-schema#}subClassOf",
    )
    parent_class_of: List[str] = Field(
        default_factory=list,
        description="{http://www.w3.org/2000/01/rdf-schema#}subClassOf",
    )
    is_defined_by: Optional[str] = Field(
        None, description="{http://www.w3.org/2000/01/rdf-schema#}isDefinedBy"
    )
    see_also: List[str] = Field(
        default_factory=list,
        description="{http://www.w3.org/2000/01/rdf-schema#}seeAlso",
    )
    comment: Optional[str] = Field(
        None, description="{http://www.w3.org/2000/01/rdf-schema#}comment"
    )
    deprecated: bool = Field(
        False, description="{http://www.w3.org/2002/07/owl#}deprecated"
    )
    preferred_label: Optional[str] = Field(
        None, description="{http://www.w3.org/2004/02/skos/core#}prefLabel"
    )
    alternative_labels: List[str] = Field(
        default_factory=list,
        description="{http://www.w3.org/2004/02/skos/core#}altLabel",
    )
    translations: Dict[str, str] = Field(
        default_factory=dict, description="translations from other languages"
    )
    hidden_label: Optional[str] = Field(
        None, description="{http://www.w3.org/2004/02/skos/core#}hiddenLabel"
    )
    definition: Optional[str] = Field(
        None, description="{http://www.w3.org/2004/02/skos/core#}definition"
    )
    examples: List[str] = Field(
        default_factory=list,
        description="{http://www.w3.org/2004/02/skos/core#}example",
    )
    notes: List[str] = Field(
        default_factory=list, description="{http://www.w3.org/2004/02/skos/core#}note"
    )
    history_note: Optional[str] = Field(
        None, description="{http://www.w3.org/2004/02/skos/core#}historyNote"
    )
    editorial_note: Optional[str] = Field(
        None, description="{http://www.w3.org/2004/02/skos/core#}editorialNote"
    )
    in_scheme: Optional[str] = Field(
        None, description="{http://www.w3.org/2004/02/skos/core#}inScheme"
    )
    identifier: Optional[str] = Field(
        None, description="{http://purl.org/dc/elements/1.1/}identifier"
    )
    description: Optional[str] = Field(
        None, description="{http://purl.org/dc/elements/1.1/}description"
    )
    source: Optional[str] = Field(
        None, description="{http://purl.org/dc/elements/1.1/}source"
    )
    country: Optional[str] = Field(
        None, description="{http://www.loc.gov/mads/rdf/v1#}country"
    )

    def is_valid(self) -> bool:
        """
        Check if the OWL class is valid.

        Returns:
            bool: True if the OWL class is valid, False otherwise.
        """
        return self.label is not None

    def __str__(self) -> str:
        return f"OWLClass(label={self.label}, iri={self.iri})"

    # pylint: disable=not-an-iterable
    def to_owl_element(self) -> lxml.etree.Element:
        """
        Convert the OWL class to an XML element.

        Returns:
            lxml.etree.Element: The XML element representing the OWL class.
        """
        # create the XML element
        owl_class = lxml.etree.Element(f"{{{NSMAP['owl']}}}Class", nsmap=NSMAP)

        # set the IRI
        owl_class.set(f"{{{NSMAP['rdf']}}}about", self.iri)

        # add the subClassOf elements
        for sub_class_of in self.sub_class_of:
            sub_class_of_element = lxml.etree.Element(
                f"{{{NSMAP['rdfs']}}}subClassOf", nsmap=NSMAP
            )
            sub_class_of_element.set(f"{{{NSMAP['rdf']}}}resource", sub_class_of)
            owl_class.append(sub_class_of_element)

        # add the isDefinedBy element
        if self.is_defined_by:
            is_defined_by_element = lxml.etree.Element(
                f"{{{NSMAP['rdfs']}}}isDefinedBy", nsmap=NSMAP
            )
            is_defined_by_element.set(f"{{{NSMAP['rdf']}}}resource", self.is_defined_by)
            owl_class.append(is_defined_by_element)

        # add the label element
        label_element = lxml.etree.Element(f"{{{NSMAP['rdfs']}}}label", nsmap=NSMAP)
        label_element.text = self.label
        owl_class.append(label_element)

        # add the alt label elements
        for alt_label in self.alternative_labels:
            alt_label_element = lxml.etree.Element(
                f"{{{NSMAP['skos']}}}altLabel", nsmap=NSMAP
            )
            alt_label_element.text = alt_label
            owl_class.append(alt_label_element)

        # add translations with xml:lang attrib
        for lang, translation in sorted(self.translations.items()):
            translation_element = lxml.etree.Element(
                f"{{{NSMAP['skos']}}}altLabel", nsmap=NSMAP
            )
            translation_element.text = translation
            translation_element.set(f"{{{NSMAP['xml']}}}lang", lang)
            owl_class.append(translation_element)

        # add the hidden label
        if self.hidden_label:
            hidden_label_element = lxml.etree.Element(
                f"{{{NSMAP['skos']}}}hiddenLabel", nsmap=NSMAP
            )
            hidden_label_element.text = self.hidden_label
            owl_class.append(hidden_label_element)

        # add the preferred label
        if self.preferred_label:
            preferred_label_element = lxml.etree.Element(
                f"{{{NSMAP['skos']}}}prefLabel", nsmap=NSMAP
            )
            preferred_label_element.text = self.preferred_label
            owl_class.append(preferred_label_element)

        # add the definition element
        if self.definition:
            definition_element = lxml.etree.Element(
                f"{{{NSMAP['skos']}}}definition", nsmap=NSMAP
            )
            definition_element.text = self.definition
            owl_class.append(definition_element)

        # add the examples elements
        for example in self.examples:
            example_element = lxml.etree.Element(
                f"{{{NSMAP['skos']}}}example", nsmap=NSMAP
            )
            example_element.text = example
            owl_class.append(example_element)

        # return the XML element
        return owl_class

    def to_owl_xml(self) -> str:
        """
        Convert the OWL class to an XML string.

        Returns:
            str: The XML string representing the OWL class.
        """
        # convert the XML element to a string
        return lxml.etree.tostring(
            self.to_owl_element(), pretty_print=True, encoding="utf-8"
        ).decode("utf-8")

    # pylint: disable=too-many-branches,too-many-statements
    def to_markdown(self) -> str:
        """
        Convert the OWL class to a markdown string.

        Returns:
            str: The markdown string representing the OWL class.
        """
        # create the markdown string
        markdown = f"# {self.label}\n\n"

        # add IRI
        markdown += f"**IRI:** {self.iri}\n\n"

        markdown += "## Labels\n\n"

        # add preferred label
        if self.preferred_label:
            markdown += f"**Preferred Label:** {self.preferred_label}\n\n"

        # add list of alternative labels
        if self.alternative_labels:
            markdown += "**Alternative Labels:**\n"
            for alt_label in self.alternative_labels:
                markdown += f"\n- {alt_label}"
            markdown += "\n\n"

        # add list of translations
        if self.translations:
            markdown += "**Translations:**\n"
            for lang, translation in sorted(self.translations.items()):
                markdown += f"\n- {lang}: {translation}"
            markdown += "\n\n"

        # add hidden label
        if self.hidden_label:
            markdown += f"**Hidden Label:** {self.hidden_label}\n\n"

        # add definition
        if self.definition:
            markdown += "## Definition\n\n"
            markdown += f"{self.definition}\n\n"

        # add examples
        if self.examples:
            markdown += "## Examples\n\n"
            for example in self.examples:
                markdown += f"- {example}\n"
            markdown += "\n"

        # add subClassOf
        if self.sub_class_of:
            markdown += "## Sub Class Of\n\n"
            for sub_class_of in self.sub_class_of:
                markdown += f"- {sub_class_of}\n"
            markdown += "\n"

        # add parentClassOf
        if self.parent_class_of:
            markdown += "## Parent Class Of\n\n"
            for parent_class_of in self.parent_class_of:
                markdown += f"- {parent_class_of}\n"
            markdown += "\n"

        # add isDefinedBy
        if self.is_defined_by:
            markdown += f"**Is Defined By:** {self.is_defined_by}\n\n"

        # add seeAlso
        if self.see_also:
            markdown += "## See Also\n\n"
            for see_also in self.see_also:
                markdown += f"- {see_also}\n"
            markdown += "\n"

        # add comment
        if self.comment:
            markdown += f"**Comment:** {self.comment}\n\n"

        # add deprecated
        markdown += f"**Deprecated:** {self.deprecated}\n\n"

        # add notes
        if self.notes:
            markdown += "## Notes\n\n"
            for note in self.notes:
                markdown += f"- {note}\n"
            markdown += "\n"

        # add historyNote
        if self.history_note:
            markdown += f"**History Note:** {self.history_note}\n\n"

        # add editorialNote
        if self.editorial_note:
            markdown += f"**Editorial Note:** {self.editorial_note}\n\n"

        # add inScheme
        if self.in_scheme:
            markdown += f"**In Scheme:** {self.in_scheme}\n\n"

        # add identifier
        if self.identifier:
            markdown += f"**Identifier:** {self.identifier}\n\n"

        # add description
        if self.description:
            markdown += f"**Description:** {self.description}\n\n"

        # add source
        if self.source:
            markdown += f"**Source:** {self.source}\n\n"

        # add country
        if self.country:
            markdown += f"**Country:** {self.country}\n\n"

        # return the markdown string
        return markdown

    def to_jsonld(self) -> dict:
        """
        Convert the OWL class to a JSON-LD string.

        Returns:
            str: The JSON-LD string representing the OWL class.
        """
        # initialize the JSON-LD dictionary
        # set up NSMAP -> @context
        jsonld_data: dict[str, Any] = {
            "@context": {
                None: "https://folio.openlegalstandard.org/",
                "dc": "http://purl.org/dc/elements/1.1/",
                "v1": "http://www.loc.gov/mads/rdf/v1#",
                "owl": "http://www.w3.org/2002/07/owl#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "folio": "https://folio.openlegalstandard.org/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "skos": "http://www.w3.org/2004/02/skos/core#",
                "xml": "http://www.w3.org/XML/1998/namespace",
            },
            "@id": self.iri,
            "@type": "owl:Class",
            "rdfs:label": self.label,
        }

        # add the isDefinedBy
        if self.is_defined_by:
            jsonld_data["rdfs:isDefinedBy"] = self.is_defined_by

        # add the seeAlso
        if self.see_also:
            jsonld_data["rdfs:seeAlso"] = []
            for see_also in self.see_also:
                jsonld_data["rdfs:seeAlso"].append(see_also)

        # add the comment
        if self.comment:
            jsonld_data["rdfs:comment"] = self.comment

        # add the deprecated
        if self.deprecated:
            jsonld_data["owl:deprecated"] = self.deprecated

        # add the prefLabel
        if self.preferred_label:
            jsonld_data["skos:prefLabel"] = self.preferred_label

        # add the altLabels
        if self.alternative_labels:
            jsonld_data["skos:altLabel"] = []
            for alt_label in self.alternative_labels:
                jsonld_data["skos:altLabel"].append(alt_label)

        # add translations
        if self.translations:
            for lang, translation in sorted(self.translations.items()):
                jsonld_data["skos:altLabel"] = []
                jsonld_data["skos:altLabel"].append(
                    {"@value": translation, "@language": lang}
                )

        # add the subClassOf
        if self.sub_class_of:
            jsonld_data["rdfs:subClassOf"] = []
            for sub_class_of in self.sub_class_of:
                jsonld_data["rdfs:subClassOf"].append({"@id": sub_class_of})

        # add skos hidden label
        if self.hidden_label:
            jsonld_data["skos:hiddenLabel"] = self.hidden_label

        # add skos definition
        if self.definition:
            jsonld_data["skos:definition"] = self.definition

        # add skos example
        if self.examples:
            jsonld_data["skos:example"] = []
            for example in self.examples:
                jsonld_data["skos:example"].append(example)

        # add skos note
        if self.notes:
            jsonld_data["skos:note"] = []
            for note in self.notes:
                jsonld_data["skos:note"].append(note)

        # add skos history note
        if self.history_note:
            jsonld_data["skos:historyNote"] = self.history_note

        # add skos editorial note
        if self.editorial_note:
            jsonld_data["skos:editorialNote"] = self.editorial_note

        # add skos in scheme
        if self.in_scheme:
            jsonld_data["skos:inScheme"] = self.in_scheme

        # add dc identifier
        if self.identifier:
            jsonld_data["dc:identifier"] = self.identifier

        # add dc description
        if self.description:
            jsonld_data["dc:description"] = self.description

        # add dc source
        if self.source:
            jsonld_data["dc:source"] = self.source

        # add v1 country
        if self.country:
            jsonld_data["v1:country"] = self.country

        # return the JSON-LD dictionary
        return jsonld_data

    def to_json(self) -> str:
        """
        Convert the OWL class to a JSON string.  This is just a
        wrapper around the pydantic method for consistency.

        Returns:
            str: The JSON string representing the OWL class.
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_string: str) -> "OWLClass":
        """
        Create an OWL class from a JSON string.  This is just a
        wrapper around the pydantic method for consistency.

        Args:
            json_string (str): The JSON string representing the OWL class.

        Returns:
            OWLClass: The OWL class created from the JSON string.
        """
        return cls.model_validate_json(json_string)
