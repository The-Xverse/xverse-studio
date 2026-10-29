# Independent scenario authoring successor review

The original findings remain in independent-review.md. Read-only successor inspection and three independent probes completed on Linux; no implementation writes by reviewer.

- SCN-I01: the exact observer deletion reproducer now returns XDLRejected / DEFINITION_REFERENCE_UNRESOLVED. It no longer produces a promoted dangling authored definition. Receipt: observer-reference-successor.json.
- Positive atomic repair: removing the observer and explicitly replacing the assessment definition in the same transaction succeeds, preserves evaluationId and unselected document bytes, and source_definitions resolves afterward. Receipt: atomic-reference-repair-successor.json.
- SCN-I02: the exact 600-level HTTP payload now returns 422 LIMIT_EXCEEDED with revision 1 and unchanged source. Receipt: http-depth-successor.json.

Inspected root-owned xdl/edit_limits.py: iterative limits (depth 64, 10,000 nodes, 64 KiB finite JSON) precede helper copies; the generic typed-edit dispatch applies them to logical assets as well. Inspected extracted source_definitions: existing snapshot digest verification remains in snapshot_definitions, while scenario transactions use the same admitted-definition reference validation after authoritative full-source validation. This does not grant execution authority or silently edit assessment definitions. No further concrete finding in the reviewed slice. Whole-suite verification and Windows acceptance are separate; Windows installation/testing remains held at user request.
