from folio import FOLIO

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()

    # Get triples by predicate
    is_defined_by_triples = folio.get_triples_by_predicate("rdfs:isDefinedBy")
    print(f"Number of rdfs:isDefinedBy triples: {len(is_defined_by_triples)}")

    # Get triples by subject
    subject_iri = "https://folio.openlegalstandard.org/RBGPkZ1oRgcP05LWQBGLEne"
    subject_triples = folio.get_triples_by_subject(subject_iri)
    print(f"\nTriples for subject {subject_iri}:")
    for triple in subject_triples[0:10]:
        print(f"- {triple[1]} {triple[2]}")

    # Get triples by object
    object_iri = "https://folio.openlegalstandard.org/R9sbuHkJC9aqDlHAgw58VSB"
    object_triples = folio.get_triples_by_object(object_iri)
    print(f"\nTriples with object {object_iri}:")
    for triple in object_triples[0:10]:
        print(f"- {triple[0]} {triple[1]}")
