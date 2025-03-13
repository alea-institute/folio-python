from folio import FOLIO

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()

    # Get parent classes
    bankruptcy_law = folio.search_by_label("Personal Bankruptcy Law")[0][0]
    parent_classes = folio.get_parents(bankruptcy_law.iri)
    print("Parent classes of Personal Bankruptcy Law:")
    for parent in parent_classes:
        print(f"- {parent.label}")

    # Get child classes
    area_of_law_iri = folio[
        "https://folio.openlegalstandard.org/RSYBzf149Mi5KE0YtmpUmr"
    ].iri
    child_classes = folio.get_children(area_of_law_iri, max_depth=1)
    print("\nDirect child classes of Area of Law:")
    for child in child_classes:
        print(f"- {child.label}")

    # Get entire subgraph
    subgraph = folio.get_subgraph(area_of_law_iri, max_depth=2)
    print(f"\nNumber of classes in Area of Law subgraph (depth 2): {len(subgraph)}")
