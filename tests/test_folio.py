# imports
import sys

# packages
import pytest

# project imports
from folio import FOLIO, FOLIOTypes, FOLIO_TYPE_IRIS, OWLClass


# set up a re-usable fixture for the FOLIO class
@pytest.fixture(scope="module")
def folio_graph():
    return FOLIO()


def test_list_branches():
    """
    Test the list_branches method of the FOLIO class.
    """
    # list branches
    branches = FOLIO.list_branches()
    assert isinstance(branches, list)
    assert len(branches) > 1
    assert "main" in branches
    assert "2.0.0" in branches


def test_list_branches_bad():
    """
    Test the list_branches method of the FOLIO class.
    """
    # list branches
    with pytest.raises(Exception):
        branches = FOLIO.list_branches(repo_owner="alea-institute-wrong-name")
        assert isinstance(branches, list)
        assert len(branches) == 0


def test_load_owl_nocache():
    """
    Test the load_owl method of the FOLIO class with the default GitHub repository.
    """
    # test with github
    ontology = FOLIO(use_cache=False)
    assert ontology is not None
    assert len(ontology) > 0

    # test via http
    ontology = FOLIO(
        source_type="http",
        http_url="https://github.com/alea-institute/FOLIO/raw/main/FOLIO.owl",
        use_cache=False,
    )
    assert ontology is not None
    assert len(ontology) > 0


def test_load_refresh():
    """
    Test the load_owl method of the FOLIO class with the default GitHub repository.
    """
    # load the ontology
    ontology = FOLIO(use_cache=True)
    assert ontology is not None
    assert len(ontology) > 0

    # refresh the ontology
    ontology.refresh()
    assert ontology is not None
    assert len(ontology) > 0


def test_load_owl_github():
    """
    Test the load_owl method of the FOLIO class with the default GitHub repository.
    """
    # load the ontology
    ontology = FOLIO.load_owl_github()
    assert ontology is not None
    assert len(ontology) > 0
    assert "owl:Ontology" in ontology


def test_bad_owl_github():
    """
    Test the load_owl method of the FOLIO class with the default GitHub repository.
    """
    # catch the exception
    with pytest.raises(Exception):
        ontology = FOLIO.load_owl_github(repo_owner="alea-institute-wrong-name")
        assert ontology is not None
        assert len(ontology) > 0
        assert "owl:Ontology" in ontology


def test_load_owl_github_branch():
    """
    Test the load_owl method of the FOLIO class with the default GitHub repository.
    """
    # load the ontology
    ontology = FOLIO.load_owl_github(repo_branch="2.0.0")
    assert ontology is not None
    assert len(ontology) > 0
    assert "owl:Ontology" in ontology


def test_load_owl_http():
    """
    Test the load_owl method of the FOLIO class with the default HTTP URL.
    """
    # load the ontology
    ontology = FOLIO.load_owl_http(
        http_url="https://github.com/alea-institute/FOLIO/raw/main/FOLIO.owl"
    )
    assert ontology is not None
    assert len(ontology) > 0
    assert "owl:Ontology" in ontology


def test_load_owl_bad_http():
    """
    Test the load_owl method of the FOLIO class with the default HTTP URL.
    """
    # catch the exception
    with pytest.raises(Exception):
        FOLIO.load_owl_http(
            http_url="https://github.com/alea-institute/FOLIO/raw/main/FOLIO.wol"
        )


def test_load_owl():
    """
    Test the load_owl method of the FOLIO class with the default HTTP URL.
    """
    # test with github
    ontology = FOLIO.load_owl(
        "github",
        github_repo_owner="alea-institute",
        github_repo_name="FOLIO",
        github_repo_branch="2.0.0",
    )
    assert ontology is not None
    assert len(ontology) > 0
    assert "owl:Ontology" in ontology

    # test with http
    ontology = FOLIO.load_owl(
        "http", http_url="https://github.com/alea-institute/FOLIO/raw/main/FOLIO.owl"
    )
    assert ontology is not None
    assert len(ontology) > 0
    assert "owl:Ontology" in ontology


def test_load_owl_bad_source():
    """
    Test the load_owl method of the FOLIO class with the default HTTP URL.
    """
    # catch the exception
    with pytest.raises(Exception):
        FOLIO.load_owl("bad")


def test_title_description(folio_graph):
    # check that we have a title and description
    assert folio_graph.title is not None
    assert "folio" in folio_graph.title.lower()
    assert folio_graph.description is not None


def test_class_count(folio_graph):
    # check that we have >18000 classes
    assert len(folio_graph.classes) > 18000


# use the fixture
def test_class_get(folio_graph):
    # test a good class by iri
    edmi = folio_graph["https://folio.openlegalstandard.org/R602916B1A80fDD28d392d3f"]
    assert edmi is not None
    assert isinstance(edmi, OWLClass)

    # get by just iri suffix
    edmi = folio_graph["R602916B1A80fDD28d392d3f"]
    assert edmi is not None
    assert isinstance(edmi, OWLClass)

    # get with prefixes
    edmi = folio_graph["folio:R602916B1A80fDD28d392d3f"]
    assert edmi is not None
    assert isinstance(edmi, OWLClass)

    edmi = folio_graph["lmss:R602916B1A80fDD28d392d3f"]
    assert edmi is not None
    assert isinstance(edmi, OWLClass)

    # test a good class by index
    class0 = folio_graph[0]
    assert class0 is not None
    assert isinstance(class0, OWLClass)

    # test a bad class
    bad_class = folio_graph["https://folio.openlegalstandard.org/abc123"]
    assert bad_class is None
    assert not isinstance(bad_class, OWLClass)

    # test bad int index
    bad_class = folio_graph[sys.maxsize - 1]
    assert bad_class is None
    assert not isinstance(bad_class, OWLClass)


def test_str(folio_graph):
    # test the string representation
    assert str(folio_graph) is not None
    assert "FOLIO" in str(folio_graph)


def test_class_markdown(folio_graph):
    # test the markdown representation
    edmi = folio_graph["R602916B1A80fDD28d392d3f"]
    edmi_md = edmi.to_markdown()
    assert "# U.S. District Court - W.D. Michigan\n" in edmi_md


def test_class_json(folio_graph):
    # test the json representation
    edmi = folio_graph["R602916B1A80fDD28d392d3f"]
    edmi_json = edmi.to_json()
    assert '"label":"U.S. District Court - W.D. Michigan"' in edmi_json


def test_class_jsonld(folio_graph):
    # test the json representation
    edmi = folio_graph["R602916B1A80fDD28d392d3f"]
    edmi_jsonld = edmi.to_jsonld()
    assert "rdfs:label" in edmi_jsonld
    assert edmi_jsonld["rdfs:label"] == "U.S. District Court - W.D. Michigan"


def test_class_xml(folio_graph):
    # test the xml representation
    edmi = folio_graph["R602916B1A80fDD28d392d3f"]
    edmi_xml = edmi.to_owl_xml()
    assert "<rdfs:label>U.S. District Court - W.D. Michigan</rdfs:label>" in edmi_xml


def test_all_formatters(folio_graph):
    for c in folio_graph.classes:
        assert c.to_markdown() is not None
        assert c.to_json() is not None
        assert c.to_owl_xml() is not None


def test_search_prefix(folio_graph):
    for c in folio_graph.search_by_prefix("Mich"):
        assert c.label == "Michigan"
        assert "US+MI" in c.alternative_labels
        break


def test_search_label(folio_graph):
    for c, score in folio_graph.search_by_label("Georgia"):
        assert "Georgia" in c.label
        assert "US+GA" in c.alternative_labels
        assert score > 0.9
        break

    for c, score in folio_graph.search_by_label("SDNY"):
        assert c.label == "U.S. District Court - S.D. New York"
        assert "S.D.N.Y." in c.alternative_labels
        assert score > 0.9
        break


def test_search_definitions(folio_graph):
    for c, score in folio_graph.search_by_definition("air"):
        assert "air" in c.definition


def test_get_types(folio_graph):
    assert len(folio_graph.get_player_actors()) > 0
    assert len(folio_graph.get_areas_of_law()) > 0
    assert len(folio_graph.get_asset_types()) > 0
    assert len(folio_graph.get_communication_modalities()) > 0
    assert len(folio_graph.get_currencies()) > 0
    assert len(folio_graph.get_data_formats()) > 0
    assert len(folio_graph.get_document_artifacts()) > 0
    assert len(folio_graph.get_engagement_terms()) > 0
    assert len(folio_graph.get_events()) > 0
    assert len(folio_graph.get_forum_venues()) > 0
    assert len(folio_graph.get_governmental_bodies()) > 0
    assert len(folio_graph.get_industries()) > 0
    assert len(folio_graph.get_languages()) > 0
    assert len(folio_graph.get_folio_types()) > 0
    assert len(folio_graph.get_legal_authorities()) > 0
    assert len(folio_graph.get_legal_entities()) > 0
    assert len(folio_graph.get_locations()) > 0
    assert len(folio_graph.get_matter_narratives()) > 0
    assert len(folio_graph.get_matter_narrative_formats()) > 0
    assert len(folio_graph.get_objectives()) > 0
    assert len(folio_graph.get_services()) > 0
    assert len(folio_graph.get_standards_compatibilities()) > 0
    assert len(folio_graph.get_statuses()) > 0
    assert len(folio_graph.get_system_identifiers()) > 0


def test_triples(folio_graph):
    # test the triples
    assert len(folio_graph.triples) > 0
    assert len(folio_graph.get_triples_by_predicate("rdfs:isDefinedBy")) > 0
    assert (
        len(
            folio_graph.get_triples_by_subject(
                "https://folio.openlegalstandard.org/RBGPkZ1oRgcP05LWQBGLEne"
            )
        )
        > 0
    )
    assert (
        len(
            folio_graph.get_triples_by_object(
                "https://folio.openlegalstandard.org/R9sbuHkJC9aqDlHAgw58VSB"
            )
        )
        > 0
    )


def test_benchmark_load(benchmark):
    @benchmark
    def load_folio():
        FOLIO()


def test_benchmark_get_areas_of_law(benchmark, folio_graph):
    @benchmark
    def get_areas_of_law():
        return folio_graph.get_areas_of_law()


def test_benchmark_get_children(benchmark, folio_graph):
    area_of_law_iri = FOLIO_TYPE_IRIS[FOLIOTypes.AREA_OF_LAW]

    @benchmark
    def get_children():
        return folio_graph.get_children(area_of_law_iri)


def test_benchmark_get_parents(benchmark, folio_graph):
    pb_iri = folio_graph.search_by_label("Personal Bankruptcy Law")[0][0].iri

    @benchmark
    def get_parents():
        return folio_graph.get_parents(pb_iri)


def test_benchmark_search_prefix(benchmark, folio_graph):
    @benchmark
    def search_prefix():
        return folio_graph.search_by_prefix("Mich")


def test_benchmark_search_labels(benchmark, folio_graph):
    @benchmark
    def search_labels():
        return folio_graph.search_by_label("Georgia")


def test_benchmark_search_definitions(benchmark, folio_graph):
    @benchmark
    def search_definitions():
        return folio_graph.search_by_definition("air")


def test_benchmark_get_triples_by_predicate(benchmark, folio_graph):
    @benchmark
    def get_triples_by_predicate():
        return folio_graph.get_triples_by_predicate("rdfs:isDefinedBy")


def test_benchmark_get_triples_by_subject(benchmark, folio_graph):
    @benchmark
    def get_triples_by_subject():
        return folio_graph.get_triples_by_subject(
            "https://folio.openlegalstandard.org/RBGPkZ1oRgcP05LWQBGLEne"
        )


def test_benchmark_get_triples_by_object(benchmark, folio_graph):
    @benchmark
    def get_triples_by_object():
        return folio_graph.get_triples_by_object(
            "https://folio.openlegalstandard.org/R9sbuHkJC9aqDlHAgw58VSB"
        )


def test_iri_generation(folio_graph):
    for i in range(10):
        iri = folio_graph.generate_iri()
        assert iri is not None
        assert iri.startswith("https://folio.openlegalstandard.org/")
        b64_token = iri.split("/")[-1]
        assert b64_token.isalnum()
        assert len(b64_token) > 16
