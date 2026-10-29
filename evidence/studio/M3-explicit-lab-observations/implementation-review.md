# Observation foundation implementation self-review

This is a component self-review, not independent milestone acceptance.

The implementation keeps installation, permission, observation, reservation and
execution authority separate. A new native object and exact permission are both
required; neither reservation scope nor incidental method presence installs a
probe. Existing lease configuration/authority/bounded-provider source is byte
identical to6183e5e. Actual compatibility tests preserve the old descriptor digest.

Original intent/key mapping commits before delegation; delegated state commits
before the fixture callback. Duplicate keys recover original receipts without
repeating contact, even after grant revocation or missing installation. Runtime
and physical commands remain unavailable. Operation reads enforce owner and a
closed projection; contradictory status/result/time/bounds fail closed. Private
binding/unknown provider fields and provider exception strings stay excluded.

One callback per observation provider ID and zero queued callbacks are allowed.
Timeout keeps its slot until actual return and discards late results. Grant
generation, binding pin and absolute deadline are rechecked before and after the
callback. Revocation cannot undo an already started observation. Provider-owned
serialization with other device operations, actual perturbation/stop semantics
and hardware conformance remain external admission obligations. The facade never
infers physical safety from a timeout, unavailable result or fixture success.

Review tightened persisted-state validation to require a result field, compatible
status/result dimensions, duplicate-free declared resources and a valid bounded
deadline. Invalid backend clock arithmetic rejects before storing intent. Tests
cover these failures, including exact post-commit read-back versus unknown final
persistence. The native SIGKILL supplement proves one real interruption point;
it does not establish the whole arbitrary-crash/physical recovery matrix.

Remaining implementation: browser controls with exact same-key pending identity,
explicit unsupported explanations, separate original clock/metadata/receipt facts,
late context/navigation/focus guards and both viewport regressions. Full current
backend/browser/package verification is required before promoting this slice.


The initial full backend1145 run ends1144pass/1campaign terminal-file assertion
failure, retained under full-backend-failed/. Controlled worker-save evidence and
the additive writer-exit precondition repair live in the separate
M4-campaign-terminal-writer-precondition dossier. All four affected cases pass;
no fresh full successor pass is claimed. Two initial browser cases fail for the
absent connection-options control. Complete configured controls, same-key recovery
and context/focus checks remain necessary; unavailable-only UI would not complete
the requested observation workflow.
