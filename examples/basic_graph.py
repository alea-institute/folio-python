from folio import FOLIO

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()

    # Get the number of classes in the ontology
    print(f"Number of classes: {len(folio)}")

    # Get ontology title and description
    print(f"Title: {folio.title}")
    print(f"Description: {folio.description}")

    # Access a class by IRI
    contract_class = folio["https://folio.openlegalstandard.org/R602916B1A80fDD28d392d3f"]
    print(f"Class: {contract_class.label}")
    print(f"Definition: {contract_class.definition}")

    # Access a class by short IRI
    edmi_class = folio["R602916B1A80fDD28d392d3f"]
    print(f"Class: {edmi_class.label}")

    # Get class by index
    first_class = folio[0]
    print(f"First class: {first_class.label}")
