# ADR-0031: Bind owned measurement faults to existing experiment-lite timing

Status: offline implementation under verification. Runtime, forms, evidence and
AC-025 acceptance remain open. T082/T083 remain in progress, including their
original dependencies. This is independent owned/offline preparation while T068
and the broader integration gates remain open; it waives no task dependency.

The selected public XDL package is xverse-xdl 0.4.0 at platform revision
`7fab6a290c3731533c2b88517158055c768b9d4e`. Native Scenario Fault activation and
recovery are opaque strings. Its experiment-lite 0.1 Profile already requires a
`fault-intent` on each native fault with a typed trigger and duration. Full public
experiment compilation rejects native faults lacking those declarations. Therefore
timing uses that existing representation. There is no second timing grammar,
schedule sidecar, executable graph or parser for arbitrary activation strings.

An explicit owned Profile `io.xverse.studio.reference-faults` 1.0.0 binds the native
fault to `state-observer`, field `measured`. Its closed payload version is `1.0`,
attached only to native Scenario faults. Fault kind `measurement-hold` and the two
exact `urn:xverse:studio:reference-faults:1.0:activation` / `recovery` markers identify
the binding; neither marker encodes time. Unknown payloads remain intact and
unsupported. Selecting or copying this schema grants no execution capability.

`compile_reference_fault_intent` compiles the entire source set with the normal
public profile-schema argument before interpreting the admitted binding. It retains
the authoritative semantic/plan identities, exact Profile/schema identities, native
fault/target identities, original trigger/duration values and units. The selected
plan v1 normalizes quantities to integer nanoseconds; the owned source-clock codec
uses exact microseconds. Both representations remain explicit and no receipt time,
rounding, clock synchronization or implicit unit conversion supplies missing time.

The offline subset requires the exact owned simulation-time declaration and fixed
step dimensionless state observer targeting the reference System's state-flow.
Only timed experiment-lite triggers are interpreted. Duration/timestep retain the
owned parameter types, seconds units, finite bounds, whole-microsecond resolution
and at most 3,000 steps. Between one and 32 uniquely identified faults may bind the
measured field. Intervals are half-open; activation and recovery must land on sample
boundaries with `0 <= activation < recovery < duration`. Recovery at the run horizon
is refused because the current model samples only before that horizon. Overlapping
intervals are refused; adjacent intervals permit recovery before the next activation
at the same boundary. These are model applicability checks, not physical authority.
The legacy `stuck-sensor` parameter cannot be combined with explicit schedules.

The intended measurement-hold model freezes the current measured value at activation
while state and control continue to evolve, then restores live measurement at recovery.
It differs from the legacy fault, which freezes the initial value from mid-run onward.
That intended runtime behavior is not implemented by this offline compiler. It needs
an explicit model artifact, provider capability/version, independently checked frozen
worker inputs, bounded requested/observed activation and recovery evidence, and actual
native/browser verification before admission. Historical model/worker behavior remains
unchanged. Native Windows, external Lite, device effects and milestone gates remain
separate obligations. No new device or physical stimulation authority is introduced.

For now the schema is supplied explicitly to the offline compiler; the default
registry and runtime do not advertise it. The result is always `compiled_intent`
with `executionAllowed: false`. Existing reference preflight still rejects the new
declarations. Verification must exercise both positive full-source compilation and
negative bindings, timing, conflicts, limits, profile identity and non-dispatch.
CLI/library identity agreement proves only compilation, not observed fault effects.
