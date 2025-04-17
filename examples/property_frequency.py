from folio import FOLIO
from collections import Counter
from typing import Dict, List, Tuple

def get_property_usage_frequency(folio: FOLIO) -> List[Tuple[str, int]]:
    """
    Analyze the frequency of object properties in the ontology.
    
    Args:
        folio: FOLIO instance
        
    Returns:
        List of tuples containing (property_label, frequency) sorted by frequency
    """
    # Get all object properties
    properties = folio.get_all_properties()
    
    # Create a map of property labels to their IRIs
    prop_label_to_iri = {}
    for prop in properties:
        if prop.label:
            prop_label_to_iri[prop.label] = prop.iri
    
    # Count occurrences of each property in triples
    property_counter = Counter()
    
    # Go through all triples and count property usage
    for triple in folio._cached_triples:
        # If the predicate matches a property label, count it
        if triple[1] in prop_label_to_iri:
            property_counter[triple[1]] += 1
    
    # Sort by frequency (highest first)
    return property_counter.most_common()

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()
    
    # Get property usage frequency
    property_frequencies = get_property_usage_frequency(folio)
    
    # Display the results
    print(f"Found {len(property_frequencies)} object properties with usage data")
    print("\nTop 20 most frequently used object properties:")
    print("-" * 60)
    print(f"{'Property Name':<40} {'Frequency':<10}")
    print("-" * 60)
    
    for prop_label, count in property_frequencies[:20]:
        print(f"{prop_label:<40} {count:<10}")
    
    print("\nLeast used object properties:")
    print("-" * 60)
    print(f"{'Property Name':<40} {'Frequency':<10}")
    print("-" * 60)
    
    for prop_label, count in property_frequencies[-10:]:
        print(f"{prop_label:<40} {count:<10}")
        
    # Get properties with no usage
    used_properties = {prop[0] for prop in property_frequencies}
    unused_properties = []
    
    for prop in folio.get_all_properties():
        if prop.label and prop.label not in used_properties:
            unused_properties.append(prop.label)
    
    print(f"\nNumber of object properties with no usage: {len(unused_properties)}")
    if unused_properties:
        print("First 10 unused properties:")
        for prop in unused_properties[:10]:
            print(f"- {prop}")