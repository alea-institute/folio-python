from folio import FOLIO

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()

    # Search for classes with "Contract" in the label
    results = folio.search_by_label("SDNY", limit=3)
    print("** Labels **")
    for owl_class, score in results:
        print(f"Class: {owl_class.label}, Score: {score}")
    print()

    # Search for classes with "legal" in the definition
    results = folio.search_by_definition("waterways", limit=3)
    print("** Definitions **")
    for owl_class, score in results:
        print(
            f"Class: {owl_class.label}, Definition: {owl_class.definition[:50]}..., Score: {score}"
        )
