from folio import FOLIO

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()

    # Get all object properties
    properties = folio.get_all_properties()
    print(f"Number of object properties in FOLIO: {len(properties)}")

    # Get a specific property by IRI
    example_property = folio.get_property("https://folio.openlegalstandard.org/R1L3IueMeHCrxnDlOU2dRg")
    print(f"\nExample property: {example_property.label}")
    print(f"IRI: {example_property.iri}")
    
    if example_property.preferred_label:
        print(f"Preferred label: {example_property.preferred_label}")
    
    if example_property.definition:
        print(f"Definition: {example_property.definition[:100]}...")
    
    if example_property.domain:
        print(f"Domain classes: {[folio[d].label for d in example_property.domain if folio[d]]}")
    
    if example_property.range:
        print(f"Range classes: {[folio[r].label for r in example_property.range if folio[r]]}")

    # Get properties by label
    print("\nSearching for properties with 'drafted' label:")
    drafted_properties = folio.get_properties_by_label("folio:drafted")
    for prop in drafted_properties:
        print(f"- {prop.label}")
        print(f"  Definition: {prop.definition[:80]}..." if prop.definition else "  No definition")
        print(f"  Alternative labels: {prop.alternative_labels}")