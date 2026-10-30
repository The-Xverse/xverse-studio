# ADR-0041: Bounded strict installed-provider descriptor validation

Status: new-work admission implemented and verified against enrolled/installed
Autoverse; T004's remaining active-control review stays open. No companion/runtime API is added.

The existing descriptor gate accepts malformed implementation identities and field
types and raises TypeError for a null capability list. Admission must verify the
v1 core before a configured provider can perform operations. Preserve compatible
provider extensions as inert bounded JSON; do not reinterpret them as commands.

Validate exact noncoerced field types, SHA256 identity, IDs, host/architecture lists,
operations, scoped capability records, legal states, closed object parameter schema,
authority requirements, physical-effects Boolean and finite nonnegative numeric
limits. Reject ambiguous repeated capability scopes and undeclared operations.
Bound a complete descriptor to64KiB,4096 JSON values and16 container levels;
unknown extension payloads remain exact JSON within those bounds. Validate parameter
schemas against the existing installed Draft2020-12 implementation without resolving
their instance references or contacting external schemas. No schema becomes code.

An incompatible/unreadable configured descriptor is projected as an unavailable
provider under its server-configured identity, with a generic typed reason and no
raw payload echo. Core authoring remains available. Do not call that provider's
readiness or new-work callback from an unavailable projection. Keep existing provider
handles for original ownership inspection/cleanup; discovery is not authority to
discard them. Revalidate descriptors for discovery and before new execution;
changed admission invalidates prior capability/snapshot identities. The post-accept
dispatch boundary must refuse a changed provider before task/worker acquisition.

Expose the versioned discovery core through generated HTTP/frontend schemas while
preserving current healthy descriptors and unavailable Lite metadata. No API/project
input can register providers. Host OS facts, Studio Linux scope and provider-specific
host support stay separate. Declared compatibility is not installation verification.

Per the user's current test instruction, use the actual enrolled Autoverse classic
and platform adapters as validation targets. Controlled malformed descriptors prove
refusal without provider operations. Actual complete-demo operation is separate
positive evidence. Preserve original operator sessions, claims and Argus bytes.
This repair alone does not establish all T004 clauses or milestone acceptance.
