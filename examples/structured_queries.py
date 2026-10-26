"""Structured-query recipes for an already loaded FOLIO graph.

Importing this module does not construct a graph or load ontology data. These
repository examples are not included in the installed folio-python package.
Use positive limits; each query returns a partial selection in stored order.
"""

from folio import FOLIO, OWLClass, OWLObjectProperty


def classes_in_branch(
    graph: FOLIO, *, text: str, branch: str, limit: int = 20
) -> list[OWLClass]:
    """Find descendants in a branch with text in any supported class text field.

    Text is a case-insensitive substring. The branch root is excluded, and
    no match (including an unknown branch) returns an empty list.
    """
    return graph.query(any_text=text, branch=branch, limit=limit)


def properties_between(
    graph: FOLIO,
    *,
    text: str,
    domain_iri: str,
    range_iri: str,
    has_inverse: bool | None = None,
    limit: int = 20,
) -> list[OWLObjectProperty]:
    """Find properties by label text and explicitly declared domain and range.

    Full or short endpoint IRIs are accepted. Text is a case-insensitive
    substring. Set has_inverse to True or False to require or exclude an
    inverse declaration; None leaves it unrestricted. No match returns [].
    Ancestor endpoint declarations do not automatically match descendants.
    """
    return graph.query_properties(
        label=text,
        domain_iri=domain_iri,
        range_iri=range_iri,
        has_inverse=has_inverse,
        limit=limit,
    )


def connections_between_branches(
    graph: FOLIO,
    *,
    source_text: str,
    source_branch: str,
    target_text: str,
    target_branch: str,
    property_text: str,
    source_limit: int = 5,
    target_limit: int = 5,
    property_limit_per_pair: int = 3,
) -> list[tuple[OWLClass, OWLObjectProperty, OWLClass]]:
    """Compose class selections with property queries into explicit associations.

    Return (source class, property, target class) tuples. A property appears
    once for each matching source/target pair. Empty class selections or no
    matching properties return []. This checks stored declarations, not
    inferred applicability or instance relationships.

    With positive limits the result has at most source_limit * target_limit *
    property_limit_per_pair rows. Limits apply independently, so this is a
    bounded sample of matches, not an exhaustive join or a relevance ranking.
    """
    sources = classes_in_branch(
        graph, text=source_text, branch=source_branch, limit=source_limit
    )
    targets = classes_in_branch(
        graph, text=target_text, branch=target_branch, limit=target_limit
    )
    connections = []
    for source in sources:
        for target in targets:
            properties = properties_between(
                graph,
                text=property_text,
                domain_iri=source.iri,
                range_iri=target.iri,
                limit=property_limit_per_pair,
            )
            for prop in properties:
                connections.append((source, prop, target))
    return connections
