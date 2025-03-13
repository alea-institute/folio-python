"""
folio/graph.py - FOLIO (Federated Open Legal Information Ontology) Python library

https://openlegalstandard.org/

This module provides a Python library for working with FOLIO (Federated Open Legal Information Ontology) data.

TODO: implement token caching layer in system prompt for search; need upstream support in alea-llm-client first
"""

# pylint: disable=fixme,no-member,unsupported-assignment-operation,too-many-lines,too-many-public-methods,invalid-name

# future import for self-referencing type hints
from __future__ import annotations

# imports
import asyncio
import base64
import hashlib
import importlib.util
import json
import time
import traceback
import uuid
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

# packages
import httpx
import lxml.etree
from alea_llm_client import BaseAIModel

# project imports
from folio.config import (
    DEFAULT_GITHUB_API_URL,
    DEFAULT_GITHUB_OBJECT_URL,
    DEFAULT_GITHUB_REPO_BRANCH,
    DEFAULT_GITHUB_REPO_NAME,
    DEFAULT_GITHUB_REPO_OWNER,
    DEFAULT_HTTP_URL,
    DEFAULT_SOURCE_TYPE,
)
from folio.logger import get_logger
from folio.models import OWLClass, NSMAP


class FOLIOTypes(Enum):
    """
    Enum for FOLIO types.
    """

    ACTOR_PLAYER = "Actor / Player"
    AREA_OF_LAW = "Area of Law"
    ASSET_TYPE = "Asset Type"
    COMMUNICATION_MODALITY = "Communication Modality"
    CURRENCY = "Currency"
    DATA_FORMAT = "Data Format"
    DOCUMENT_ARTIFACT = "Document / Artifact"
    ENGAGEMENT_TERMS = "Engagement Terms"
    EVENT = "Event"
    FORUMS_VENUES = "Forums and Venues"
    GOVERNMENTAL_BODY = "Governmental Body"
    INDUSTRY = "Industry"
    LANGUAGE = "Language"
    FOLIO_TYPE = "FOLIO Type"
    LEGAL_AUTHORITIES = "Legal Authorities"
    LEGAL_ENTITY = "Legal Entity"
    LOCATION = "Location"
    MATTER_NARRATIVE = "Matter Narrative"
    MATTER_NARRATIVE_FORMAT = "Matter Narrative Format"
    OBJECTIVES = "Objectives"
    SERVICE = "Service"
    STANDARDS_COMPATIBILITY = "Standards Compatibility"
    STATUS = "Status"
    SYSTEM_IDENTIFIERS = "System Identifiers"


FOLIO_TYPE_IRIS = {
    FOLIOTypes.ACTOR_PLAYER: "R8CdMpOM0RmyrgCCvbpiLS0",
    FOLIOTypes.AREA_OF_LAW: "RSYBzf149Mi5KE0YtmpUmr",
    FOLIOTypes.ASSET_TYPE: "RCIwc6WJi6IT7xePURxsi4T",
    FOLIOTypes.COMMUNICATION_MODALITY: "R8qItBwG2pRMFhUq1HQEMnb",
    FOLIOTypes.CURRENCY: "R767niCLQVC5zIcO5WDQMSl",
    FOLIOTypes.DATA_FORMAT: "R79aItNTJQwHgR002wuX3iC",
    FOLIOTypes.DOCUMENT_ARTIFACT: "RDt4vQCYDfY0R9fZ5FNnTbj",
    FOLIOTypes.ENGAGEMENT_TERMS: "R9kmGZf5FSmFdouXWQ1Nndm",
    FOLIOTypes.EVENT: "R73hoH1RXYjBTYiGfolpsAF",
    FOLIOTypes.FORUMS_VENUES: "RBjHwNNG2ASVmasLFU42otk",
    FOLIOTypes.GOVERNMENTAL_BODY: "RBQGborh1CfXanGZipDL0Qo",
    FOLIOTypes.INDUSTRY: "RDIwFaFcH4KY0gwEY0QlMTp",
    FOLIOTypes.LANGUAGE: "RDOvAHsvY8TKJ1O1orXPM9o",
    FOLIOTypes.FOLIO_TYPE: "R8uI6AZ9vSgpAdKmfGZKfTZ",
    FOLIOTypes.LEGAL_AUTHORITIES: "RC1CZydjfH8oiM4W3rCkma3",
    FOLIOTypes.LEGAL_ENTITY: "R7L5eLIzH0CpOUE74uJvSjL",
    FOLIOTypes.LOCATION: "R9aSzp9cEiBCzObnP92jYFX",
    FOLIOTypes.MATTER_NARRATIVE: "R7ReDY2v13rer1U8AyOj55L",
    FOLIOTypes.MATTER_NARRATIVE_FORMAT: "R8ONVC8pLVJC5dD4eKqCiZL",
    FOLIOTypes.OBJECTIVES: "RlNFgB3TQfMzV26V4V7u4E",
    FOLIOTypes.SERVICE: "RDK1QEdQg1T8B5HQqMK2pZN",
    FOLIOTypes.STANDARDS_COMPATIBILITY: "RB4cFSLB4xvycDlKv73dOg6",
    FOLIOTypes.STATUS: "Rx69EnEj3H3TpcgTfUSoYx",
    FOLIOTypes.SYSTEM_IDENTIFIERS: "R8EoZh39tWmXCkmP2Xzjl6E",
}

OWL_THING = "http://www.w3.org/2002/07/owl#Thing"

# Default cache directory for the ontology
DEFAULT_CACHE_DIR: Path = Path.home() / ".folio" / "cache"

# Default maximum depth for subgraph traversal safety
DEFAULT_MAX_DEPTH: int = 16

# IRI max generation attempt for safety.
MAX_IRI_ATTEMPTS: int = 16

# default max tokens to return from LLM
DEFAULT_MAX_TOKENS: int = 1024

# default max depth for parallel search
DEFAULT_SEARCH_MAX_DEPTH = 2

# minimum length for prefix search
MIN_PREFIX_LENGTH: int = 3

# Set up logger
LOGGER = get_logger(__name__)

# try to import rapidfuzz and marisa_trie with importlib; log if not able to.
try:
    if importlib.util.find_spec("rapidfuzz") is not None:
        import rapidfuzz
    else:
        LOGGER.warning("Disabling search functionality: rapidfuzz not found.")
        rapidfuzz = None

    if importlib.util.find_spec("marisa_trie") is not None:
        import marisa_trie
    else:
        LOGGER.warning("Disabling search functionality: marisa_trie not found.")
        marisa_trie = None

    if importlib.util.find_spec("alea_llm_client") is not None:
        import alea_llm_client
        from alea_llm_client.llms.prompts.sections import (
            format_prompt,
            format_instructions,
        )
    else:
        LOGGER.warning("Disabling search functionality: alea_llm_client not found.")
        alea_llm_client = None
except ImportError as e:
    LOGGER.warning("Failed to check for search functionality: %s", e)
    rapidfuzz = None
    marisa_trie = None


# pylint: disable=too-many-instance-attributes
class FOLIO:
    """
    FOLIO (Federated Open Legal Information Ontology) Python library

    This class provides a Python library for working with FOLIO (Federated Open Legal Information Ontology) data.
    """

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        source_type: str = DEFAULT_SOURCE_TYPE,
        http_url: Optional[str] = DEFAULT_HTTP_URL,
        github_repo_owner: str = DEFAULT_GITHUB_REPO_OWNER,
        github_repo_name: str = DEFAULT_GITHUB_REPO_NAME,
        github_repo_branch: str = DEFAULT_GITHUB_REPO_BRANCH,
        use_cache: bool = True,
        llm: Optional[BaseAIModel] = None,
    ) -> None:
        """
        Initialize the FOLIO ontology.

        Args:
            source_type (str): The source type for loading the ontology. Either "github" or "http".
            http_url (Optional[str]): The HTTP URL for the ontology.
            github_repo_owner (str): The owner of the GitHub repository.
            github_repo_name (str): The name of the GitHub repository.
            github_repo_branch (str): The branch of the GitHub repository.
            use_cache (bool): Whether to use the local cache
            llm (Optional[BaseAIModel]): an alea_llm_client BaseAIModel instance for searching via decoder

        Returns:
            None
        """
        # initialize the tree and parser
        self.source_type: str = source_type
        self.http_url: Optional[str] = http_url
        self.github_repo_owner: str = github_repo_owner
        self.github_repo_name: str = github_repo_name
        self.github_repo_branch: str = github_repo_branch
        self.use_cache: bool = use_cache

        # initialize the tree and parser
        self.tree: Optional[lxml.etree._Element] = None
        self.parser: Optional[lxml.etree.XMLParser] = None

        # ontology data structures
        self.title: Optional[str] = None
        self.description: Optional[str] = None
        self.classes: List[OWLClass] = []
        self.iri_to_index: Dict[str, int] = {}
        self.label_to_index: Dict[str, List[int]] = {}
        self.alt_label_to_index: Dict[str, List[int]] = {}
        self.class_edges: Dict[str, List[str]] = {}
        self._cached_triples: Tuple[Tuple[str, str, str], ...] = ()
        self._label_trie: Optional[marisa_trie.Trie] = None
        self._prefix_cache: Dict[str, List[OWLClass]] = {}
        self.triples: List[Tuple[str, str, str]] = []

        # load the ontology
        LOGGER.info("Loading FOLIO ontology from %s...", source_type)
        start_time = time.time()
        owl_buffer = FOLIO.load_owl(
            source_type=source_type,
            http_url=http_url,
            github_repo_owner=github_repo_owner,
            github_repo_name=github_repo_name,
            github_repo_branch=github_repo_branch,
            use_cache=use_cache,
        )
        end_time = time.time()
        LOGGER.info("Loaded FOLIO ontology in %.2f seconds", end_time - start_time)

        # parse the ontology
        LOGGER.info("Parsing FOLIO ontology...")
        start_time = time.time()
        self.parse_owl(owl_buffer)
        end_time = time.time()
        LOGGER.info("Parsed FOLIO ontology in %.2f seconds", end_time - start_time)

        # try to initialize a model
        self.llm: Optional[BaseAIModel] = None
        if alea_llm_client is not None:
            try:
                if llm is None:
                    self.llm = alea_llm_client.OpenAIModel(model="gpt-4o")
                else:
                    self.llm = llm
                LOGGER.info("Initialized LLM model: %s", self.llm)
            except Exception:  # pylint: disable=broad-except
                LOGGER.warning(
                    "Failed to initialize LLM model: %s", traceback.format_exc()
                )

    @staticmethod
    def list_branches(
        repo_owner: str = DEFAULT_GITHUB_REPO_OWNER,
        repo_name: str = DEFAULT_GITHUB_REPO_NAME,
    ) -> List[str]:
        """
        List the branches in a GitHub repository.

        Args:
            repo_owner (str): The owner of the GitHub repository.
            repo_name (str): The name of the GitHub repository.

        Returns:
            List[str]: A list of branch names in the GitHub repository.
        """
        # GitHub API endpoint for listing branches
        url = f"{DEFAULT_GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/branches"

        # Set up headers with authentication
        headers = {"Accept": "application/vnd.github.v3+json"}

        try:
            # setup client in context handler and make the request
            with httpx.Client() as client:
                LOGGER.info("Listing branches for %s/%s", repo_owner, repo_name)
                response = client.get(url, headers=headers)

                # Check if the request was successful
                response.raise_for_status()

                # Parse and return the branches
                branches = response.json()
                return [branch["name"] for branch in branches]
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Error listing branches for {repo_owner}/{repo_name}"
            ) from e

    @staticmethod
    def load_cache(
        cache_path: str | Path = DEFAULT_CACHE_DIR,
        source_type: str = DEFAULT_SOURCE_TYPE,
        http_url: Optional[str] = DEFAULT_HTTP_URL,
        github_repo_owner: str = DEFAULT_GITHUB_REPO_OWNER,
        github_repo_name: str = DEFAULT_GITHUB_REPO_NAME,
        github_repo_branch: str = DEFAULT_GITHUB_REPO_BRANCH,
    ) -> Optional[str]:
        """
        Load the FOLIO ontology from a local cache.

        Args:
            cache_path (str | Path): The path to the cache directory.
            source_type (str): The source type for loading the ontology. Either "github" or "http".
            http_url (Optional[str]): The HTTP URL for the ontology.
            github_repo_owner (str): The owner of the GitHub repository.
            github_repo_name (str): The name of the GitHub repository.
            github_repo_branch (str): The branch of the GitHub repository.

        Returns:
            str | None: The raw ontology buffer, or None if the cache file does not exist.
        """
        # determine the cache file path
        if isinstance(cache_path, str):
            cache_root_path = Path(cache_path)
        else:
            cache_root_path = cache_path

        # determine the cache file name
        if source_type == "github":
            cache_key = f"{github_repo_owner}/{github_repo_name}/{github_repo_branch}"
        elif source_type == "http":
            if http_url is None:
                raise ValueError("HTTP URL must be provided for source type 'http'.")
            cache_key = http_url
        else:
            raise ValueError("Invalid source type. Must be either 'github' or 'http'.")

        # hash the cache key
        cache_key_hash = hashlib.blake2b(cache_key.encode()).hexdigest()
        cache_file_path = cache_root_path / source_type / f"{cache_key_hash}.owl"

        # create the cache directory if it does not exist
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)

        # check if the cache file exists
        if cache_file_path.exists():
            LOGGER.info("Loaded ontology from cache: %s", cache_file_path)
            with cache_file_path.open("rt", encoding="utf-8") as input_file:
                return input_file.read()

        # return None if the cache file does not exist
        LOGGER.info("Cache file does not exist: %s", cache_file_path)
        return None

    @staticmethod
    def save_cache(
        buffer: str,
        cache_path: str | Path = DEFAULT_CACHE_DIR,
        source_type: str = DEFAULT_SOURCE_TYPE,
        http_url: Optional[str] = DEFAULT_HTTP_URL,
        github_repo_owner: str = DEFAULT_GITHUB_REPO_OWNER,
        github_repo_name: str = DEFAULT_GITHUB_REPO_NAME,
        github_repo_branch: str = DEFAULT_GITHUB_REPO_BRANCH,
    ) -> None:
        """
        Save the FOLIO ontology to a local cache.

        Args:
            buffer (str): The raw ontology buffer.
            cache_path (str | Path): The path to the cache directory.
            source_type (str): The source type for loading the ontology. Either "github" or "http".
            http_url (Optional[str]): The HTTP URL for the ontology.
            github_repo_owner (str): The owner of the GitHub repository.
            github_repo_name (str): The name of the GitHub repository.
            github_repo_branch (str): The branch of the GitHub repository.
        """
        # determine the cache file path
        if isinstance(cache_path, str):
            cache_root_path = Path(cache_path)
        else:
            cache_root_path = cache_path

        # determine the cache file name
        if source_type == "github":
            cache_key = f"{github_repo_owner}/{github_repo_name}/{github_repo_branch}"
        elif source_type == "http":
            if http_url is None:
                raise ValueError("HTTP URL must be provided for source type 'http'.")
            cache_key = http_url
        else:
            raise ValueError("Invalid source type. Must be either 'github' or 'http'.")

        # hash the cache key
        cache_key_hash = hashlib.blake2b(cache_key.encode()).hexdigest()
        cache_file_path = cache_root_path / source_type / f"{cache_key_hash}.owl"

        # create the cache directory if it does not exist
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)

        # write the buffer to the cache file
        with cache_file_path.open("wt", encoding="utf-8") as output_file:
            LOGGER.info("Saving to cache: %s", cache_file_path)
            output_file.write(buffer)

    @staticmethod
    def load_owl_github(
        repo_owner: str = DEFAULT_GITHUB_REPO_OWNER,
        repo_name: str = DEFAULT_GITHUB_REPO_NAME,
        repo_branch: str = DEFAULT_GITHUB_REPO_BRANCH,
    ) -> str:
        """
        Load the FOLIO ontology in OWL format from a GitHub repository.

        Args:
            repo_owner (str): The owner of the GitHub repository.
            repo_name (str): The name of the GitHub repository.
            repo_branch (str): The branch of the GitHub repository.
        """
        # GitHub URL for the ontology file
        url = f"{DEFAULT_GITHUB_OBJECT_URL}/{repo_owner}/{repo_name}/{repo_branch}/FOLIO.owl"

        # Load the ontology from the GitHub URL
        try:
            # setup client in context handler and make the request
            with httpx.Client() as client:
                LOGGER.info(
                    "Loading ontology from %s/%s/%s", repo_owner, repo_name, repo_branch
                )
                response = client.get(url)

                # Check if the request was successful
                response.raise_for_status()

                # return the raw ontology buffer
                return response.text
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Error loading ontology from {repo_owner}/{repo_name}/{repo_branch}"
            ) from e

    @staticmethod
    def load_owl_http(http_url: Optional[str] = DEFAULT_HTTP_URL) -> str:
        """
        Load the FOLIO ontology in OWL format from an HTTP URL.

        Args:
            http_url (str): The HTTP URL for the ontology.
        """
        # Load the ontology from the HTTP URL
        try:
            # setup client in context handler and make the request
            with httpx.Client(follow_redirects=True) as client:
                LOGGER.info("Loading ontology from %s", http_url)
                response = client.get(http_url)

                # Check if the request was successful
                response.raise_for_status()

                # return the raw ontology buffer
                return response.text
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Error loading ontology from {http_url}") from e

    @staticmethod
    def load_owl(
        source_type: str = DEFAULT_SOURCE_TYPE,
        http_url: Optional[str] = DEFAULT_HTTP_URL,
        github_repo_owner: str = DEFAULT_GITHUB_REPO_OWNER,
        github_repo_name: str = DEFAULT_GITHUB_REPO_NAME,
        github_repo_branch: str = DEFAULT_GITHUB_REPO_BRANCH,
        use_cache: bool = True,
    ) -> str:
        """
        Load the FOLIO ontology in OWL format.

        Args:
            source_type (str): The source type for loading the ontology. Either "github" or "http".
            http_url (Optional[str]): The HTTP URL for the ontology.
            github_repo_owner (str): The owner of the GitHub repository.
            github_repo_name (str): The name of the GitHub repository.
            github_repo_branch (str): The branch of the GitHub repository.
            use_cache (bool): Whether to use the local cache.
        """
        owl_buffer: Optional[str] = None
        if use_cache:
            # Load the ontology from the cache
            owl_buffer = FOLIO.load_cache(
                source_type=source_type,
                http_url=http_url,
                github_repo_owner=github_repo_owner,
                github_repo_name=github_repo_name,
                github_repo_branch=github_repo_branch,
            )

        if not owl_buffer:
            if source_type == "github":
                # Load the ontology from GitHub
                owl_buffer = FOLIO.load_owl_github(
                    repo_owner=github_repo_owner,
                    repo_name=github_repo_name,
                    repo_branch=github_repo_branch,
                )
            elif source_type == "http":
                if http_url is None:
                    raise ValueError(
                        "HTTP URL must be provided for source type 'http'."
                    )

                # Load the ontology from an HTTP URL
                owl_buffer = FOLIO.load_owl_http(http_url=http_url)
            else:
                raise ValueError(
                    "Invalid source type. Must be either 'github' or 'http'."
                )

        # Save the ontology to the cache
        if use_cache:
            FOLIO.save_cache(
                buffer=owl_buffer,
                source_type=source_type,
                http_url=http_url,
                github_repo_owner=github_repo_owner,
                github_repo_name=github_repo_name,
                github_repo_branch=github_repo_branch,
            )

        return owl_buffer

    @staticmethod
    @cache
    def get_ns_tag(ns: str, tag: str) -> str:
        """
        Get the namespace tag for an XML element.

        Args:
            ns (str): The namespace.
            tag (str): The tag name.

        Returns:
            str: The namespace tag.
        """
        # DO NOT use nested f-strings for this method; not supported in older Python versions.
        if ns in NSMAP:
            return "{%s}%s" % (NSMAP[ns], tag)

        return tag

    # pylint: disable=too-many-branches,too-many-statements
    def parse_owl_class(self, node: lxml.etree._Element) -> None:
        """
        Parse an OWL class in the FOLIO ontology.

        Args:
            node (lxml.etree._Element): The node element.

        Returns:
            OWLClass | None: The parsed OWL class, or None if the class is invalid.
        """
        # get the rdf:about
        iri = node.attrib.get(self.get_ns_tag("rdf", "about"), None)
        if iri is None:
            LOGGER.info("Missing IRI for OWL class: %s", node)
            return

        # initialize the OWL class
        owl_class = OWLClass(iri=iri)

        for child in node.getchildren():
            if child.tag == self.get_ns_tag("rdfs", "label"):
                # set label
                owl_class.label = child.text

                # add triple
                self.triples.append((owl_class.iri, "rdfs:label", child.text))
            elif child.tag == self.get_ns_tag("rdfs", "subClassOf"):
                # set parent class
                parent_class = child.attrib.get(
                    self.get_ns_tag("rdf", "resource"), None
                )
                if parent_class:
                    owl_class.sub_class_of.append(parent_class)

                    # add triple
                    self.triples.append(
                        (owl_class.iri, "rdfs:subClassOf", parent_class)
                    )
            elif child.tag == self.get_ns_tag("rdfs", "isDefinedBy"):
                # set defined by
                defined_by = child.attrib.get(self.get_ns_tag("rdf", "resource"), None)
                if defined_by:
                    owl_class.is_defined_by = defined_by

                    # add triple
                    self.triples.append((owl_class.iri, "rdfs:isDefinedBy", defined_by))
            elif child.tag == self.get_ns_tag("rdfs", "seeAlso"):
                # set see also
                see_also = child.attrib.get(self.get_ns_tag("rdf", "resource"), None)
                if see_also:
                    owl_class.see_also.append(child.text)

                    # add triple
                    self.triples.append((owl_class.iri, "rdfs:seeAlso", see_also))
            elif child.tag == self.get_ns_tag("rdfs", "comment"):
                # set comment
                owl_class.comment = child.text

                # add triple
                self.triples.append((owl_class.iri, "rdfs:comment", child.text))
            elif child.tag == self.get_ns_tag("owl", "deprecated"):
                # set deprecated
                owl_class.deprecated = True

                # add triple
                self.triples.append((owl_class.iri, "owl:deprecated", "true"))
            elif child.tag == self.get_ns_tag("skos", "prefLabel"):
                # set preferred label
                owl_class.preferred_label = child.text

                # add triple
            elif child.tag == self.get_ns_tag("skos", "altLabel"):
                # set alternative label
                lang = child.attrib.get(self.get_ns_tag("xml", "lang"), None)
                if lang:
                    owl_class.translations[lang] = child.text
                else:
                    owl_class.alternative_labels.append(child.text)

                # add triple
                self.triples.append((owl_class.iri, "skos:altLabel", child.text))
            elif child.tag == self.get_ns_tag("skos", "hiddenLabel"):
                # set hidden label
                owl_class.hidden_label = child.text

                # add to alternative labels
                owl_class.alternative_labels.append(child.text)

                # add triple
                self.triples.append((owl_class.iri, "skos:hiddenLabel", child.text))
            elif child.tag == self.get_ns_tag("skos", "definition"):
                # set definition
                owl_class.definition = child.text

                # add triple
                self.triples.append((owl_class.iri, "skos:definition", child.text))
            elif child.tag == self.get_ns_tag("skos", "example"):
                # add example
                owl_class.examples.append(child.text)

                # add triple
                self.triples.append((owl_class.iri, "skos:example", child.text))
            elif child.tag == self.get_ns_tag("skos", "note"):
                # add note
                owl_class.notes.append(child.text)

                # add triple
                self.triples.append((owl_class.iri, "skos:note", child.text))
            elif child.tag == self.get_ns_tag("skos", "historyNote"):
                # set history note
                owl_class.history_note = child.text

                # add triple
                self.triples.append((owl_class.iri, "skos:historyNote", child.text))
            elif child.tag == self.get_ns_tag("skos", "editorialNote"):
                # set editorial note
                owl_class.editorial_note = child.text

                # add triple
                self.triples.append((owl_class.iri, "skos:editorialNote", child.text))
            elif child.tag == self.get_ns_tag("skos", "inScheme"):
                # set in scheme
                owl_class.in_scheme = child.text

                # add triple
                self.triples.append((owl_class.iri, "skos:inScheme", child.text))
            elif child.tag == self.get_ns_tag("dc", "identifier"):
                # set identifier
                owl_class.identifier = child.text

                # add triple
                self.triples.append((owl_class.iri, "dc:identifier", child.text))
            elif child.tag == self.get_ns_tag("dc", "description"):
                # set description
                owl_class.description = child.text

                # add triple
                self.triples.append((owl_class.iri, "dc:description", child.text))
            elif child.tag == self.get_ns_tag("dc", "source"):
                # set source
                owl_class.source = child.text

                # add triple
                self.triples.append((owl_class.iri, "dc:source", child.text))
            elif child.tag == self.get_ns_tag("v1", "country"):
                # set country
                owl_class.country = child.text

                # add triple
                self.triples.append((owl_class.iri, "v1:country", child.text))
            else:
                # raise RuntimeError(f"Unknown tag: {child.tag}")
                LOGGER.debug("Unknown tag: %s", child.tag)

        # skip invalid classes
        if not owl_class.is_valid() and owl_class.iri != OWL_THING:
            LOGGER.info("Invalid OWL class: %s", owl_class)
            return

        # append and update indices
        self.classes.append(owl_class)

        # update the indices
        index = len(self.classes) - 1
        self.iri_to_index[owl_class.iri] = index

        # update the label index with pref label
        if owl_class.label:
            if owl_class.label not in self.label_to_index:
                self.label_to_index[owl_class.label] = [index]
            else:
                self.label_to_index[owl_class.label].append(index)

        # update the label index with alt labels
        for alt_label in owl_class.alternative_labels:  # pylint: disable=not-an-iterable
            if alt_label:
                if alt_label not in self.alt_label_to_index:
                    self.alt_label_to_index[alt_label] = [index]
                else:
                    self.alt_label_to_index[alt_label].append(index)

    def parse_owl_ontology(self, node: lxml.etree._Element) -> None:
        """
        Parse an OWL ontology in the FOLIO ontology.

        Args:
            node (lxml.etree._Element): The node element.

        Returns:
            None
        """
        for child in node.getchildren():
            if child.tag == self.get_ns_tag("dc", "title"):
                self.title = child.text
            elif child.tag == self.get_ns_tag("dc", "description"):
                self.description = child.text

    def parse_node(self, node: lxml.etree._Element) -> None:
        """
        Parse a node in the FOLIO ontology.

        Switch on these types:
            - owl:Class
            - owl:ObjectProperty
            - owl:DatatypeProperty
            - owl:AnnotationProperty
            - owl:NamedIndividual
            - owl:Ontology
            - rdf:Description

        Args:
            node (lxml.etree._Element): The node element.

        Returns:
            None
        """
        if node.tag == self.get_ns_tag("owl", "Class"):
            self.parse_owl_class(node)
        elif node.tag == self.get_ns_tag("owl", "Ontology"):
            self.parse_owl_ontology(node)
        elif node.tag == self.get_ns_tag("owl", "ObjectProperty"):
            # TODO: parse object property
            pass
        elif node.tag == self.get_ns_tag("owl", "DatatypeProperty"):
            # TODO: parse datatype property
            pass
        elif node.tag == self.get_ns_tag("owl", "AnnotationProperty"):
            # TODO: parse annotation property
            pass
        elif node.tag == self.get_ns_tag("owl", "NamedIndividual"):
            # TODO: parse named individual
            pass
        elif node.tag == self.get_ns_tag("rdf", "Description"):
            # TODO: parse rdf description
            pass
        else:
            LOGGER.debug("Unknown node type: %s", node.tag)

    def parse_owl(self, buffer: str) -> None:
        """
        Parse the FOLIO ontology in OWL format.

        Args:
            buffer (str): The raw ontology buffer.

        Returns:
            lxml.etree.ElementTree: The parsed ontology tree.
        """
        # initialize the parser
        self.parser = lxml.etree.XMLParser(
            encoding="utf-8", remove_comments=True, ns_clean=True
        )

        # parse the buffer into a tree
        self.tree = lxml.etree.fromstring(buffer, parser=self.parser)

        # parse node types
        for node in self.tree.iterchildren():
            self.parse_node(node)

        # build the class edges
        for owl_class in self.classes:
            for parent_class in owl_class.sub_class_of:
                # skip owl thing
                if parent_class == OWL_THING:
                    continue

                # add forward edge
                if parent_class not in self.class_edges:
                    self.class_edges[parent_class] = []
                self.class_edges[parent_class].append(owl_class.iri)

                # add reverse edge to the parent class
                if parent_class in self:
                    self[parent_class].parent_class_of.append(owl_class.iri)  # type: ignore
                else:
                    LOGGER.warning("Parent class not found: %s", parent_class)

        # freeze triple tuples
        self._cached_triples = tuple(self.triples)

        # now create the Trie for the labels in label_to_index and alt_label_to_index
        if marisa_trie is not None:
            all_labels = [
                label
                for label in list(self.label_to_index.keys())
                + list(self.alt_label_to_index.keys())
                if len(label) >= MIN_PREFIX_LENGTH
            ]
            self._label_trie = marisa_trie.Trie(all_labels)

    def get_subgraph(
        self, iri: str, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Recursive function to get the subgraph of the FOLIO ontology.

        Args:
            iri (str): The IRI of the OWL class to start from.
            max_depth (int): The maximum depth to traverse the graph.

        Returns:
            List[OWLClass]: The subgraph of the FOLIO ontology.
        """
        # get the index of the class
        index = self.iri_to_index.get(self.normalize_iri(iri), None)
        if index is None:
            return []

        # get the class
        owl_class = self.classes[index]

        # initialize the subgraph
        subgraph = [owl_class]

        # traverse the graph
        if max_depth != 0:
            for child_class in owl_class.parent_class_of:
                subgraph.extend(self.get_subgraph(child_class, max_depth - 1))

        return subgraph

    def get_children(
        self, iri: str, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the children of an OWL class in the FOLIO ontology.

        Args:
            iri (str): The IRI of the OWL class to start from.
            max_depth (int): The maximum depth to traverse the graph.

        Returns:
            List[OWLClass]: The children of the OWL class.
        """
        return [
            child for child in self.get_subgraph(iri, max_depth) if child != self[iri]
        ]

    def get_parents(
        self, iri: str, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the parents of an OWL class in the FOLIO ontology.

        Args:
            iri (str): The IRI of the OWL class to start from.
            max_depth (int): The maximum depth to traverse the graph.

        Returns:
            List[OWLClass]: The parents of the OWL class.
        """
        # get the index of the class
        index = self.iri_to_index.get(self.normalize_iri(iri), None)
        if index is None:
            return []

        # get the class
        owl_class = self.classes[index]

        # initialize the subgraph
        subgraph = [owl_class]

        # traverse the graph backwards
        if max_depth != 0:
            for parent_class in owl_class.sub_class_of:
                subgraph.extend(self.get_parents(parent_class, max_depth - 1))

        return subgraph

    @staticmethod
    @cache
    def normalize_iri(iri: str) -> str:
        """
        Normalize an IRI by removing the FOLIO prefix or by handling legacy IRIs.

        Args:
            iri (str): The IRI to normalize.

        Returns:
            str: The normalized IRI.
        """
        if iri.startswith("https://folio.openlegalstandard.org/"):
            return iri

        # Legacy support for SOLI URLs
        # Legacy support - redirect old URLs
        if iri.startswith("https://soli.openlegalstandard.org/"):
            return iri.replace(
                "https://soli.openlegalstandard.org/",
                "https://folio.openlegalstandard.org/",
            )

        if iri.startswith("folio:"):
            iri = iri[len("folio:") :]

        # Legacy support for 'soli:' prefix
        if iri.startswith("soli:"):
            iri = iri[len("soli:") :]

        if iri.startswith("lmss:"):
            iri = iri[len("lmss:") :]

        if iri.startswith("http://lmss.sali.org/"):
            iri = iri[len("http://lmss.sali.org/") :]

        if iri.count("/") == 0:
            return f"https://folio.openlegalstandard.org/{iri}"

        return iri

    def __contains__(self, item: str) -> bool:
        """
        Check if an OWL class is in the FOLIO ontology.

        Args:
            item (str): The IRI of the OWL class.

        Returns:
            bool: True if the OWL class is in the ontology, False otherwise.
        """
        return self.normalize_iri(item) in self.iri_to_index

    def __getitem__(self, item: str | int) -> Optional[OWLClass]:
        """
        Get an OWL class by index (int) or IRI (str).

        Args:
            item (str | int): The index or IRI of the OWL class.

        Returns:
            OWLClass | None: The OWL class, or None if the class is not found.
        """
        if isinstance(item, int):
            try:
                return self.classes[item]
            except IndexError:
                return None
        elif isinstance(item, str):
            index = self.iri_to_index.get(self.normalize_iri(item), None)
            if index is not None:
                return self.classes[index]
            return None
        else:
            raise TypeError("Invalid item type. Must be str or int.")

    def get_by_label(
        self, label: str, include_alt_labels: bool = False
    ) -> List[OWLClass]:
        """
        Get an OWL class by label.

        Args:
            label (str): The label of the OWL class.
            include_alt_labels (bool): Whether to include alternative labels.

        Returns:
            List[OWLClass]: The list of OWL classes with the given label.
        """
        classes = [self[index] for index in self.label_to_index.get(label, [])]
        if include_alt_labels:
            classes.extend(
                [self[index] for index in self.alt_label_to_index.get(label, [])]
            )

        return classes  # type: ignore

    def get_by_alt_label(
        self, alt_label: str, include_hidden_labels: bool = True
    ) -> List[OWLClass]:
        """
        Get an OWL class by alternative label.

        Args:
            alt_label (str): The alternative label of the OWL class.
            include_hidden_labels (bool): Whether to include hidden labels.

        Returns:
            List[OWLClass]: The list of OWL classes with the given alternative label.
        """
        classes = [self[index] for index in self.alt_label_to_index.get(alt_label, [])]
        if include_hidden_labels:
            classes.extend(
                [self[index] for index in self.label_to_index.get(alt_label, [])]
            )

        return classes  # type: ignore

    def refresh(self) -> None:
        """
        Refresh the FOLIO ontology.

        Returns:
            None
        """
        # clear the ontology data structures
        self.title = None
        self.description = None
        self.classes.clear()
        self.iri_to_index.clear()
        self.label_to_index.clear()
        self.alt_label_to_index.clear()
        self.class_edges.clear()
        self.triples.clear()
        self._cached_triples = ()

        # load the ontology
        LOGGER.info("Refreshing FOLIO ontology with use_cache=False...")
        start_time = time.time()
        owl_buffer = FOLIO.load_owl(
            source_type=self.source_type,
            http_url=self.http_url,
            github_repo_owner=self.github_repo_owner,
            github_repo_name=self.github_repo_name,
            github_repo_branch=self.github_repo_branch,
            use_cache=False,
        )
        end_time = time.time()
        LOGGER.info("Refreshed FOLIO ontology in %.2f seconds", end_time - start_time)

        # parse the ontology
        LOGGER.info("Parsing FOLIO ontology...")
        start_time = time.time()
        self.parse_owl(owl_buffer)
        end_time = time.time()
        LOGGER.info("Parsed FOLIO ontology in %.2f seconds", end_time - start_time)

    def search_by_prefix(self, prefix: str) -> List[OWLClass]:
        """
        Search for IRIs by prefix.

        Args:
            prefix (str): The prefix to search for.

        Returns:
            List[OWLClass]: The list of OWL classes with IRIs that start with the prefix.
        """
        # check for cache
        if prefix in self._prefix_cache:
            return self._prefix_cache[prefix]

        # search in trie
        if marisa_trie is not None:
            # return in sorted by length ascending list
            keys = sorted(
                self._label_trie.keys(prefix),
                key=len,
            )
        else:
            # search with pure python
            keys = sorted(
                [
                    label
                    for label in list(self.label_to_index.keys())
                    + list(self.alt_label_to_index.keys())
                    if label.startswith(prefix)
                ],
                key=len,
            )

        # get the list of IRIs
        iri_list = []
        for key in keys:
            iri_list.extend(self.label_to_index.get(key, []))
            iri_list.extend(self.alt_label_to_index.get(key, []))

        # materialize and cache
        classes = [self[index] for index in iri_list]
        self._prefix_cache[prefix] = classes

        # return the classes
        return classes

    @staticmethod
    @cache
    def _basic_search(
        query: str,
        search_list: Tuple[str],
        limit: int = 10,
        search_type: Literal["string", "token"] = "string",
    ) -> List[Tuple[str, int | float, int]]:
        """
        Basic search function using rapidfuzz.

        Args:
            query (str): The search query.
            search_list (List[str]): The list of strings to search.
            limit (int): The maximum number of results to return.
            search_type (str): The type of search to perform. Either "string" or "token".

        Returns:
            List[Tuple[str, int | float, int]]: The list of search results with
                the string, the search score, and the index.
        """
        return sorted(
            rapidfuzz.process.extract(  # type: ignore
                query,
                search_list,
                scorer=rapidfuzz.fuzz.WRatio
                if search_type == "string"
                else rapidfuzz.fuzz.partial_token_set_ratio,
                processor=rapidfuzz.utils.default_process,
                limit=limit,
            ),
            # sort first by score, then by length of text
            key=lambda x: (-x[1], len(x[0])),
        )

    def search_by_label(
        self, label: str, include_alt_labels: bool = True, limit: int = 10
    ) -> List[Tuple[OWLClass, int | float]]:
        """
        Search for an OWL class by label.

        Args:
            label (str): The label to search for.
            include_alt_labels (bool): Whether to include alternative labels.
            limit (int): The maximum number of results to return.

        Returns:
            List[Tuple[OWLClass, int | float]]: The list of search results with
                the OWL class and the search score.
        """
        # check if we can search
        if rapidfuzz is None:
            raise RuntimeError(
                "search extra must be installed to use search functions: pip install folio-python[search]"
            )

        # get search labels
        if not include_alt_labels:
            search_labels = tuple(self.label_to_index.keys())
        else:
            search_labels = tuple(
                list(self.label_to_index.keys()) + list(self.alt_label_to_index.keys())
            )

        # use basic rapidfuzz convenience function for this
        results = []
        seen_classes = set()
        for search_label, score, _ in self._basic_search(
            label, search_labels, limit=limit, search_type="string"
        ):
            label_classes = self.get_by_label(
                search_label, include_alt_labels=include_alt_labels
            )
            for label_class in label_classes:
                if label_class.iri not in seen_classes:
                    seen_classes.add(label_class.iri)
                    results.append((label_class, score))

                if len(results) >= limit:
                    break

        return results

    def search_by_definition(
        self, definition: str, limit: int = 10
    ) -> List[Tuple[OWLClass, int | float]]:
        """
        Search for an OWL class by definition.

        Args:
            definition (str): The definition to search for.
            limit (int): The maximum number of results to return.

        Returns:
            List[Tuple[OWLClass, int | float]]: The list of search results with
                the OWL class and the search score.
        """
        # check if we can search
        if rapidfuzz is None:
            raise RuntimeError(
                "search extra must be installed to use search functions: pip install folio-python[search]"
            )

        # get definitions to search with zip pattern
        class_index, class_definitions = zip(
            *[
                (i, c.definition)
                for i, c in enumerate(self.classes)
                if c.definition is not None
            ]
        )

        # use basic rapidfuzz convenience function for this
        results = []
        for _, score, search_index in self._basic_search(
            definition, class_definitions, limit=limit, search_type="token"
        ):
            results.append((self.classes[class_index[search_index]], score))
            if len(results) >= limit:
                break

        return results

    def format_classes_for_llm(
        self,
        owl_classes: List[OWLClass],
    ) -> str:
        """
        Format a list of OWL classes for an LLM.

        Args:
            owl_classes (List[OWLClass]): The list of OWL classes.

        Returns:
            str: The formatted LLM input.
        """
        return "\n".join(
            json.dumps(
                {
                    k: v
                    for k, v in {
                        "iri": owl_class.iri,
                        "label": owl_class.label,
                        "preferred_label": owl_class.preferred_label,
                        "definition": owl_class.definition,
                        "alt_labels": owl_class.alternative_labels,
                        "parents": [
                            self[parent_iri].preferred_label or self[parent_iri].label
                            for parent_iri in owl_class.sub_class_of
                        ],
                    }.items()
                    if v
                }
            )
            for owl_class in owl_classes
        )

    async def search_by_llm(
        self,
        query: str,
        search_set: List[OWLClass],
        limit: int = 10,
        scale: int = 10,
        include_reason: bool = False,
    ) -> List[Tuple[OWLClass, int | float]]:
        """
        Search for an OWL class by LLM.

        Args:
            query (str): The query to search for.
            search_set (List[OWLClass]): The list of OWL classes to search.
            limit (int): The maximum number of results to return.
            scale (int): The scale for the LLM relevancy scoring.
            include_reason (bool): Whether to include the reason for the search.

        Returns:
            List[Tuple[OWLClass, int | float]]: The list of search results with
                the OWL class and the search score.
        """
        # skip if we don't have llm
        if self.llm is None:
            raise RuntimeError(
                "search extra must be installed to use llm search functions: pip install folio-python[search]"
            )

        # set up instructions based on args
        instructions = [
            "Think carefully about the intent and context of the QUERY.",
            f"Score the relevance of the ITEMS above to the QUERY below on a scale from 1 to {scale}.",
            "Only score items that are directly relevant to the query.",
            f"Include up to the {limit} most relevant items.",
            "Include a brief explanation for why you believe each item is relevant."
            if include_reason
            else "",
            "Return the items identified by iri in order from most relevant to least relevant.",
            "If there are no relevant items, return an empty list.",
            "Respond in JSON.  Carefully adhere to the SCHEMA below.",
        ]

        # set up the schema
        if include_reason:
            schema = """{"results": [{"iri": string, "relevance": integer, "explanation": string}]}"""
        else:
            schema = """{"results": [{"iri": string, "relevance": integer}]}"""

        # format the prompt
        prompt = format_prompt(
            {
                "items": self.format_classes_for_llm(search_set),
                "instructions": format_instructions(
                    [
                        instruction
                        for instruction in instructions
                        if len(instruction.strip()) > 0
                    ]
                ),
                "query": query,
                "schema": schema,
            }
        )

        # get the response
        try:
            llm_response = await self.llm.json_async(
                prompt,
                system="You are a legal knowledge management platform searching for relevant items in a taxonomy.\n"
                "Always respond in JSON according to SCHEMA.",
                max_tokens=DEFAULT_MAX_TOKENS,
            )
            llm_response_data = llm_response.data

            # parse the results
            if isinstance(llm_response_data, dict) and "results" in llm_response_data:
                llm_results = llm_response_data["results"]
            elif isinstance(llm_response_data, list):
                llm_results = llm_response_data
            else:
                llm_results = []

            # filter and return the results
            seen_iris = set()
            search_results = []
            for result in llm_results:
                iri = result.get("iri", None)
                if iri and iri not in seen_iris and iri in self.iri_to_index:
                    seen_iris.add(iri)
                    if include_reason:
                        search_results.append(
                            (
                                self[iri],
                                result.get("relevance", 0),
                                result.get("explanation", ""),
                            )
                        )
                    else:
                        search_results.append((self[iri], result.get("relevance", 0)))

            return sorted(search_results, key=lambda x: -x[1])[:limit]
        except Exception as e:
            LOGGER.error("Error searching with LLM: %s", traceback.format_exc())
            raise RuntimeError("Error searching with LLM.") from e

    async def parallel_search_by_llm(
        self,
        query: str,
        search_sets: Optional[List[List[OWLClass]]] = None,
        limit: int = 10,
        scale: int = 10,
        include_reason: bool = False,
        max_depth: int = DEFAULT_SEARCH_MAX_DEPTH,
    ) -> List[Tuple[OWLClass, int | float]]:
        """
        Parallel search using gather() pattern across one or more search sets.

        Args:
            query (str): The query to search for.
            search_sets (List[List[OWLClass]]): The list of search sets to search; if None, use all classes.
            limit (int): The maximum number of results to return.
            scale (int): The scale for the LLM relevancy scoring.
            include_reason (bool): Whether to include the reason for the search.
            max_depth (int): The maximum depth to search for classes if search_sets is None.

        Returns:
            List[Tuple[OWLClass, int | float]]: The list of search results with
                the OWL class and the search score.
        """
        # skip if we don't have llm
        if self.llm is None:
            raise RuntimeError(
                "search extra must be installed to use llm search functions: pip install folio-python[search]"
            )

        # get the search sets
        if search_sets is None:
            search_sets = list(self.get_folio_branches(max_depth=max_depth).values())

        # get the responses
        try:
            # gather across the search sets
            search_set_results = await asyncio.gather(
                *[
                    self.search_by_llm(
                        query,
                        search_set,
                        limit=limit,
                        scale=scale,
                        include_reason=include_reason,
                    )
                    for search_set in search_sets
                ]
            )

            # flatten the results and sort again
            search_results = sorted(
                [
                    search_result
                    for search_set_result in search_set_results
                    for search_result in search_set_result
                ],
                key=lambda x: -x[1],
            )

            return search_results[:limit]
        except Exception as e:
            LOGGER.error("Error searching with LLM: %s", traceback.format_exc())
            raise RuntimeError("Error searching with LLM.") from e

    def __len__(self) -> int:
        """
        Get the number of classes in the FOLIO ontology.

        Returns:
            int: The number of classes in the FOLIO ontology.
        """
        return len(self.classes)

    def __str__(self) -> str:
        """
        Get the string representation of the FOLIO ontology.

        Returns:
            str: The string representation of the FOLIO ontology.
        """
        if self.source_type == "github":
            return f"FOLIO <{self.source_type}/{self.github_repo_owner}/{self.github_repo_name}/{self.github_repo_branch}>"

        if self.source_type == "http":
            return f"FOLIO <{self.source_type}/{self.http_url}>"

        return "FOLIO <unknown>"

    def get_player_actors(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the player actors in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of player actors.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.ACTOR_PLAYER], max_depth=max_depth
        )

    def get_areas_of_law(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the areas of law in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of areas of law.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.AREA_OF_LAW], max_depth=max_depth
        )

    def get_asset_types(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the asset types in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of asset types.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.ASSET_TYPE], max_depth=max_depth
        )

    def get_communication_modalities(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the communication modalities in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of communication modalities.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.COMMUNICATION_MODALITY], max_depth=max_depth
        )

    def get_folio_branches(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> Dict[str, List[OWLClass]]:
        """
        Get the FOLIO branches in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of FOLIO branches.
        """
        return {
            folio_type: self.get_children(folio_type_iri, max_depth=max_depth)
            for folio_type, folio_type_iri in FOLIO_TYPE_IRIS.items()
        }

    def get_currencies(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the currencies in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of currencies.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.CURRENCY], max_depth=max_depth
        )

    def get_data_formats(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the data formats in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of data formats.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.DATA_FORMAT], max_depth=max_depth
        )

    def get_document_artifacts(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the document artifacts in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of document artifacts.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.DOCUMENT_ARTIFACT], max_depth=max_depth
        )

    def get_engagement_terms(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the engagement terms in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of engagement terms.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.ENGAGEMENT_TERMS], max_depth=max_depth
        )

    def get_events(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the events in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of events.
        """
        return self.get_children(FOLIO_TYPE_IRIS[FOLIOTypes.EVENT], max_depth=max_depth)

    def get_forum_venues(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the forum venues in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of forum venues.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.FORUMS_VENUES], max_depth=max_depth
        )

    def get_governmental_bodies(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the governmental bodies in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of governmental bodies.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.GOVERNMENTAL_BODY], max_depth=max_depth
        )

    def get_industries(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the industries in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of industries.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.INDUSTRY], max_depth=max_depth
        )

    def get_languages(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the languages in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of languages.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.LANGUAGE], max_depth=max_depth
        )

    def get_folio_types(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the FOLIO types in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of FOLIO types.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.FOLIO_TYPE], max_depth=max_depth
        )

    def get_legal_authorities(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the legal authorities in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of legal authorities.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.LEGAL_AUTHORITIES], max_depth=max_depth
        )

    def get_legal_entities(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the legal entities in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of legal entities.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.LEGAL_ENTITY], max_depth=max_depth
        )

    def get_locations(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the locations in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of locations.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.LOCATION], max_depth=max_depth
        )

    def get_matter_narratives(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the matter narratives in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of matter narratives.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.MATTER_NARRATIVE], max_depth=max_depth
        )

    def get_matter_narrative_formats(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the matter narrative formats in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of matter narrative formats.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.MATTER_NARRATIVE_FORMAT], max_depth=max_depth
        )

    def get_objectives(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the objectives in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of objectives.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.OBJECTIVES], max_depth=max_depth
        )

    def get_services(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the services in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of services.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.SERVICE], max_depth=max_depth
        )

    def get_standards_compatibilities(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the standards compatibilities in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of standards compatibilities.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.STANDARDS_COMPATIBILITY], max_depth=max_depth
        )

    def get_statuses(self, max_depth: int = DEFAULT_MAX_DEPTH) -> List[OWLClass]:
        """
        Get the statuses in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of statuses.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.STATUS], max_depth=max_depth
        )

    def get_system_identifiers(
        self, max_depth: int = DEFAULT_MAX_DEPTH
    ) -> List[OWLClass]:
        """
        Get the system identifiers in the FOLIO ontology.

        Returns:
            List[OWLClass]: The list of system identifiers.
        """
        return self.get_children(
            FOLIO_TYPE_IRIS[FOLIOTypes.SYSTEM_IDENTIFIERS], max_depth=max_depth
        )

    @staticmethod
    @cache
    def _filter_triples(
        triples: Tuple[Tuple[str, str, str], ...],
        value: str,
        filter_by: str = "predicate",
    ) -> List[Tuple[str, str, str]]:
        """
        Filter triples by predicate.

        Args:
            triples (Tuple[Tuple[str, str, str], ...]): The list of triples.
            value (str): The value to filter by.
            predicate (str): The predicate to filter by.

        Returns:
            List[Tuple[str, str, str]]: The filtered list of triples.
        """
        if filter_by == "predicate":
            return [triple for triple in triples if triple[1] == value]

        if filter_by == "subject":
            return [triple for triple in triples if triple[0] == value]

        if filter_by == "object":
            return [triple for triple in triples if triple[2] == value]

        raise ValueError(
            "Invalid filter_by value. Must be 'predicate', 'subject', or 'object'."
        )

    def get_triples_by_subject(self, subject: str) -> List[Tuple[str, str, str]]:
        """
        Get triples by subject.

        Args:
            subject (str): The subject to filter by.

        Returns:
            List[Tuple[str, str, str]]: The list of triples.
        """
        return self._filter_triples(self._cached_triples, subject, filter_by="subject")

    def get_triples_by_predicate(self, predicate: str) -> List[Tuple[str, str, str]]:
        """
        Get triples by predicate.

        Args:
            predicate (str): The predicate to filter by.

        Returns:
            List[Tuple[str, str, str]]: The list of triples.
        """
        return self._filter_triples(
            self._cached_triples, predicate, filter_by="predicate"
        )

    def get_triples_by_object(self, obj: str) -> List[Tuple[str, str, str]]:
        """
        Get triples by object.

        Args:
            obj (str): The object to filter by.

        Returns:
            List[Tuple[str, str, str]]: The list of triples.
        """
        return self._filter_triples(self._cached_triples, obj, filter_by="object")

    def generate_iri(self) -> str:
        """
        Generate a new IRI for the FOLIO ontology.

        NOTE: This is designed to approximate the WebProtege IRI generation algorithm.

        Returns:
            str: The new IRI.
        """

        for _ in range(MAX_IRI_ATTEMPTS):
            # generate a new base uuid4 value
            base_value = uuid.uuid4()

            # only use alphanumeric characters from restricted b64 encdoding to
            base64_value = "".join(
                [
                    c
                    for c in base64.urlsafe_b64encode(base_value.bytes)
                    .decode("utf-8")
                    .rstrip("=")
                    if c.isalnum()
                ]
            )

            # ensure it's unique
            if base64_value in self.iri_to_index:
                continue

            return f"https://folio.openlegalstandard.org/{base64_value}"

        raise RuntimeError("Failed to generate a unique IRI.")
