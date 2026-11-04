# Numeric comparison evidence admission

The comparison decoder now checks its admitted evidence interpretation before
assigning numeric units, quantities, clocks or coverage. Unsupported sources retain
their original integrity, status and frozen configuration, with
`COMPARISON_EVIDENCE_UNSUPPORTED` and no interpreted numeric observations. Original
record inspection/playback remains available. No source evidence is rewritten.

The [inert counterexample](false-positive-before.json) previously reported an unknown
provider's reference-shaped values as compatible. The same counterexample is now
[blocked](false-positive-after.json). Separately, decoded copies of the actual
Autoverse source acquired reference-specific unit metadata before repair. These
are controlled decoder inputs, not an arbitrary-client exploit, raw tampering or
newly observed measurements. The actual source is the retained 93-record demo;
all original DB/snapshot/journal bytes remain unchanged.

Source `73039ef5370d4a3a238364158ec0ebd93aed5a4d` passes 62 focused checks. The new
cases cover unknown source/scope/reader/context, forged support declarations,
equal null/empty/numeric identifiers, missing digest, actual Autoverse and labelled
decoded-copy negatives. The known codec and its historical reader/journal omission
remain compatible. A mixed known/unknown pair preserves baseline values and
configuration differences while blocking pairing. All 84 original comparison-report
assertion ASTs are unchanged; their decoder fixture now explicitly names the
known codec instead of silently inheriting it from sample shape.

Review also reproduces a separate quality error: original Autoverse status
`available` was being interpreted as incomplete under the reference vocabulary.
Unsupported sources now keep that vocabulary uninterpreted. Known reference
`partial` evidence still blocks every field, and original reader integrity checks
remain independent for all sources. The failed actual case and passing known-codec
control are retained before the repair. [Phase reports](phases.json) and the
[attempt qualifications](attempts.json) distinguish all failures and successors.

The existing native comparison browser case passes at 1024×768 and 1440×900. It
verifies configuration differences, the new blocker and supported next action,
focus and absence of overflow. Its original retained-acknowledgement/foreign-child
response fixture remains explicit; no new admission or Start occurs. A separate
fresh 22-case native playback cohort passes at both sizes, preserving all 21 actual
telemetry receipt records, keyboard controls, paging, time absence and read failure/
context safeguards. These are read-only browser results, not fresh simulator runs.

All 543 selected repository inputs match committed Git and remain unchanged across
the final focused, comparison and playback stages. Only two production comparison
files change; runtime/provider, evaluator, compiler and frontend sources are
unchanged. All 79 frontend/build inputs and six actual native UI assets match the
preceding exact reproduction build; no new UI build is claimed. Native backends
and browser drivers exit and copied roots release. Original canonical bytes and
execution ledger counts remain unchanged.

Architecture, planning-package, descriptive platform baseline, new-file lint and
the recorded legacy-file F821/F401 checks pass. Compact legacy style is retained;
this is not a whole-file style-cleanliness claim. Native reference-workload tests
requiring new execution are explicitly NOT_RUN and retain their assertions.
No fresh full regression, performance, packaging, Windows or milestone result is
inferred from the selected checks. The prior finite benchmark keeps its own source
and execution scope.

**Counts remain 71 completed / 19 in progress / 10 blocked; zero accepted milestones.**
T091/T097 stay in progress. A successful current rerun still needs the unchanged
CARLA/GPU startup prerequisite. Complete comparison/clock/workflow acceptance,
current Windows, other engines, hardware, human/AT and full M0–M4 gates remain open.
