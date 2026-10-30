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

## Active-control follow-up under implementation

An active installed-provider input callback must use the exact verified frozen
provider identity, current valid description, availability and host compatibility.
Verify the sealed snapshot before the callback; metadata is not ownership. Apply
this to acquire/frame/release, including duplicate frames: release also publishes
controls and must not enter an unverified callback. A refused request leaves the
driver owner/mailbox unchanged; its original short lease expires independently.
Refusal explains Stop/Cancel and fresh preflight rather than inventing renewed
authority. Provider-specific field validation remains in its admitted adapter.

Fresh non-cleanup lifecycle commands also require installed-provider compatibility
inside acceptance. Existing same-key command receipts remain historical and do not
delegate again. Stop/Cancel continue through the original ownership/state/signature
checks even while fresh provider admission or the independent snapshot is invalid.
Historical read-only evidence remains available through its admitted reader.

Reject nonfinite/unencodable JSON at the generic input API boundary before lookup
or provider contact, as already required for command parameters. This introduces
no vehicle schema or industry dispatch in shared runtime-control code. Confirm
with actual Autoverse runtime controls, typed refusal, mailbox invariance, recorded
native publication and original owned cleanup; do not mark a fabricated run active.

The installed v1 binding must also implement the callbacks used by this Studio
facade: compatible readiness/optional metadata/owner-close signatures, unique
controls within declared operations, a finite UTF-8 private installation object
bounded to1MiB, and a backend-task factory or bounded Python module identity.
Advertised normalized input requires its compatible callable. Check shape without
invoking lifecycle, importing the worker or publishing private installation data.
Incompatible bindings become unavailable; authoring remains usable. This is the
existing Studio native callback protocol, not a new companion platform API.

Requested native enrollment also fails independently of core startup. If the
Autoverse tools or optional platform build are unavailable, retain a server-created
unavailable observation with a bounded typed reason and no executable binding.
A platform enrollment failure preserves a healthy classic adapter. Do not expose
raw probe exceptions or paths. Core storage, migration and server startup errors
remain fatal; this recovery applies only to optional integration enrollment.
Actual native launcher tests reproduce both missing-tool and missing-build failures
before the repair and verify authoring/compilation plus blocked preflight afterward.
