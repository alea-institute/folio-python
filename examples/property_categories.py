from folio import FOLIO
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

def categorize_properties_by_domain_range(folio: FOLIO) -> Dict[Tuple[str, str], List[str]]:
    """
    Categorizes object properties by their domain and range types.
    
    Args:
        folio: FOLIO instance
        
    Returns:
        Dictionary mapping (domain_type, range_type) pairs to lists of property labels
    """
    # Get all object properties
    properties = folio.get_all_properties()
    
    # Dictionary to store property categories
    categories = defaultdict(list)
    
    # Process each property
    for prop in properties:
        if not prop.label or not prop.domain or not prop.range:
            continue
        
        # Get domain and range class labels
        domain_labels = []
        for domain_iri in prop.domain:
            domain_class = folio[domain_iri]
            if domain_class and domain_class.label:
                domain_labels.append(domain_class.label)
        
        range_labels = []
        for range_iri in prop.range:
            range_class = folio[range_iri]
            if range_class and range_class.label:
                range_labels.append(range_class.label)
        
        # If we have valid domain and range labels, categorize the property
        if domain_labels and range_labels:
            for domain_label in domain_labels:
                for range_label in range_labels:
                    categories[(domain_label, range_label)].append(prop.label)
    
    return categories

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()
    
    # Get property categories
    categories = categorize_properties_by_domain_range(folio)
    
    # Display the results
    print(f"Found {len(categories)} domain-range categories for object properties")
    
    # Sort categories by number of properties (most first)
    sorted_categories = sorted(
        categories.items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    print("\nTop domain-range categories with the most properties:")
    print("-" * 80)
    print(f"{'Domain':<30} {'Range':<30} {'Count':<8} {'Examples'}")
    print("-" * 80)
    
    for (domain, range_val), props in sorted_categories[:15]:
        examples = ", ".join(props[:3])
        if len(props) > 3:
            examples += "..."
        print(f"{domain:<30} {range_val:<30} {len(props):<8} {examples}")
    
    # Find all properties that connect specific classes
    actor_domain_props = {}
    
    for (domain, range_val), props in categories.items():
        if "Actor" in domain:
            if range_val not in actor_domain_props:
                actor_domain_props[range_val] = set()
            actor_domain_props[range_val].update(props)
    
    print("\nRelationships from Actor/Player to other entities:")
    print("-" * 80)
    for range_val, props in sorted(actor_domain_props.items(), key=lambda x: len(x[1]), reverse=True):
        prop_list = ", ".join(sorted(list(props))[:5])
        if len(props) > 5:
            prop_list += "..."
        print(f"{range_val:<30} {len(props):<8} {prop_list}")