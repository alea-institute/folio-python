from folio import FOLIO

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()

    # Get all areas of law
    areas_of_law = folio.get_areas_of_law()
    print("** Areas of Law:**")
    for area in areas_of_law:
        print(f"- {area.label}")
    print()

    # Only top level
    areas_of_law = folio.get_areas_of_law(max_depth=1)
    print("** Top Level Areas of Law:**")
    for area in areas_of_law:
        print(f"- {area.label}")
    print()

    # Get all legal entities
    legal_entities = folio.get_legal_entities()
    print("\nLegal Entities:")
    for entity in legal_entities:
        print(f"- {entity.label}")
    print()
