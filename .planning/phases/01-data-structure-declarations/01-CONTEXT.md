# Phase 1: Data Structure Declarations - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

FOLIOGraph has all new attributes declared so subsequent phases can populate and query them.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

</decisions>

<code_context>
## Existing Code Insights

### Key Locations
- `folio/graph.py:217` — `_label_trie` attribute declaration
- `folio/graph.py:218` — `_prefix_cache` attribute declaration
- New attributes should be declared alongside existing trie/cache attributes

### Established Patterns
- Optional typing with `Optional[marisa_trie.Trie]` for trie attributes
- Empty dict `{}` for cache initialization
- Type hints using `Dict[str, List[int]]` pattern

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Declare:
- `_lowercase_label_trie: Optional[marisa_trie.Trie] = None`
- `_lowercase_to_original: Dict[str, List[str]] = {}`
- `_ci_prefix_cache: Dict[str, List[OWLClass]] = {}`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
