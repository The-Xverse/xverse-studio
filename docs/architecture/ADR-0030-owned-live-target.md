# ADR-0030: Explicit live target input of the owned reference model

Status: implementation under verification; no live-tuning acceptance yet.
Amends the owned provider contract, without changing task IDs or requirements.

The pinned XDL core and experiment-lite profile admit parameter mutability
`constant|configuration|scenario`. They do not define a runtime enum. Studio
therefore introduces an explicit owned Profile, `io.xverse.studio.reference-controls`
version 1.0, validated through the existing public XDL profile-schema mechanism.
An instance declaration enables one mutable model input, `target`, initialized from the frozen target
configuration. The native configuration parameter remains unchanged. Constant
initial parameters cannot initialize a mutable control. Other model inputs and
unrecognized declarations remain unsupported. This is a Profile extension, not a
new resource family or an implied platform runtime API.

Binding this schema alone remains inert and admits no model input. Its exact
Profile identity is validated and its bytes stay in authoritative identities;
only that recognized inert Profile is omitted from the executable-template
comparison when no input is declared.

The opt-in live-target blueprint identifies the corresponding model artifact.
Existing blueprints retain their controls. Owned provider 1.2.0 admits
`set_parameter` only when the frozen snapshot has this exact profile/declaration
and the descriptor has the matching scoped nonphysical capability. Its parameters
are `{inputId: "target", expectedValue, value}` with finite dimensionless values
in [-100,100]. The existing command CAS, current ownership and one pending command
checks apply. At most 32 mutations may apply in a run. The worker independently
checks the signed request, state/version, old value, declaration and bound.

A permitted change updates the model input at a step boundary, including while
paused. It advances the worker state version without changing lifecycle. The
original snapshot and requested/effective compilation identities remain intact;
later draft edits do not affect it. Durable operation and canonical command
completion evidence retain old/new values, requesting principal, authority,
simulation tick and recorded time. Same-key retry retains the exact payload and
operation. Missing acknowledgement is not permission to reapply a change.
Application status and evidence integrity remain independent under failure.

The HTTP command boundary verifies finite UTF-8 JSON before request
fingerprinting. The strict body model's `allow_inf_nan=False` does not inspect
`Any`-valued nested parameters. Explicit validation therefore rejects nonfinite
and unencodable parameters as422 before lookup/ledger effects, preserving valid
opaque JSON. Semantic/capability checks and independent worker limits remain
separate. This repairs a reproduced500 without weakening canonical identity.

The browser persists mutation parameters with its existing pending receipt,
retains same-key recovery, and identifies current observed versus proposed values.
Stale state or old value requires explicit review, never a silent new request.

Clock encodings are unchanged; the closed owned-reference codecs additionally
admit version 1.2.0. Provider/schema/model identities and compatibility metadata
must be refreshed, preserving external pins and unavailable runtime admission.
Native Linux and browser verification must show actual changed observations,
immutable snapshots/drafts, bounds, constant/unsupported denial, CAS/concurrency,
same-key retry and provenance. Fixtures do not establish native Windows, external
Lite, physical effects or milestone acceptance.
