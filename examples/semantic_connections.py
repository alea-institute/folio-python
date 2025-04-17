from folio import FOLIO

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()

    # Find a property with domain and range for demonstration
    test_property = None
    for prop in folio.get_all_properties():
        if prop.domain and prop.range and prop.label:
            test_property = prop
            break
    
    if not test_property:
        print("No suitable property found for demonstration")
        exit(1)
    
    # Display the property we'll use for demonstration
    print(f"Using property: {test_property.label}")
    domain_class = folio[test_property.domain[0]]
    range_class = folio[test_property.range[0]]
    print(f"Domain: {domain_class.label if domain_class else test_property.domain[0]}")
    print(f"Range: {range_class.label if range_class else test_property.range[0]}")
    
    # Find connections from a specific subject class
    if domain_class:
        print(f"\nFinding connections from {domain_class.label}:")
        connections = folio.find_connections(
            subject_class=domain_class,
            property_name=test_property
        )
        if connections:
            for i, (subject, property_obj, object_class) in enumerate(connections[:5]):
                print(f"{i+1}. {subject.label} {property_obj.label} {object_class.label}")
        else:
            print("No explicit connections found")
    
    # Example of finding all occurrences of a specific relationship type
    print("\nFinding examples of the 'observed' relationship:")
    observed_properties = folio.get_properties_by_label("folio:observed")
    if observed_properties:
        observed_property = observed_properties[0]
        # Find connections using this property (potentially across multiple domain/range pairs)
        connections = []
        for domain in observed_property.domain:
            domain_connections = folio.find_connections(
                subject_class=domain,
                property_name=observed_property
            )
            connections.extend(domain_connections)
        
        # Show the connections found
        if connections:
            for i, (subject, property_obj, object_class) in enumerate(connections[:5]):
                print(f"{i+1}. {subject.label} {property_obj.label} {object_class.label}")
        else:
            print("No explicit 'observed' connections found")
    else:
        print("No 'observed' property found")