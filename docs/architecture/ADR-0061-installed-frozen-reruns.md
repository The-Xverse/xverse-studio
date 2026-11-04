# ADR-0061 — Fresh admission of installed historical inputs

Date: 2026-11-04. Status: implemented; admission/browser components verified, full native rerun unproven.

The frozen rerun endpoint previously admitted only the executable reference
provider. Add a closed opt-in `rerunContract` 1.0 for registered native providers.
Imported descriptors, evidence and profiles cannot install a provider or grant
execution authority. Original observation playback remains read-only.

The contract requires exact frozen sources, current full preflight, no physical
effects and explicitly uncontrolled reproducibility. It enumerates supported
historical provider versions. The original protected snapshot and source-run
binding must verify; the provider ID, contract, evidence scope and installation
digest must match the current registration. The current compiler and provider
must reproduce the original plan, semantic digest and effective configuration.
Implementation identity can change, but cannot substitute a different installation
or silently change the original workload. Seeds, simulator clock alignment and
determinism are not established by a rerun.

Extract the existing complete preflight construction from its persistence wrapper.
Ordinary draft and campaign preflights retain their existing checks. An installed
rerun uses the same builder for profiles, connections, deployment, observation
contracts/budgets and provider readiness. Its acceptance transaction treats active,
unknown and unreconciled occupancy as busy. It does not read a worker or reconcile
ownership inside that transaction. A blocked attempt retains no execution intent,
child, snapshot or idempotency receipt. A later explicit request can check again.

Successful admission writes a new protected snapshot and commits its full preflight,
rerun operation and child dispatch intent in one metadata transaction. A crash before
commit can leave an unreferenced file; it grants no Start authority. Lineage references the original run,
snapshot and digest, while the new snapshot records current compiler/provider and
capabilities. The current draft never replaces historical inputs. Filesystem
rollback removes only the native directory identity acquired by this attempt.
Existing Start independently rechecks readiness and exclusive installation
ownership after the acceptance commit. A completed rerun operation acknowledges
child creation, not successful execution, a passing assertion or reproducibility.

Accepted same-key retries return the original operation without new admission.
Durable child Start mapping reconciles lost acknowledgement. An intent with no
acknowledged child stays unknown after restart and never automatically replays
Start. Existing operation and UI acknowledgement semantics remain unchanged.

The browser exposes the generic frozen-rerun admission request for recorded runs.
Unsupported providers receive a backend refusal. A child acknowledgement must
match the selected run's provider and evidence scope, as well as its original
operation/run/snapshot/project identities; reference-only browser checks no longer
hide admitted installed providers. Unknown or foreign replies retain their key.

Classic Autoverse opts in for its existing 0.3.0 and 0.4.0 source mappings on the
same enrolled installation. Platform mode stays unadmitted. This does not authorize
other installations, hardware or companion repository changes. Verification uses
copies of complete actual Autoverse recordings, read-only native admission and a
separate complete rerun in the approved isolated environment. Comparison still
blocks unsupported external telemetry quantities and source-clock alignment.
T091 and full acceptance remain open until the corresponding evidence is recorded;
native Windows remains unverified.

Traces: T091; FR-059/FR-060; AC-029. Existing task IDs and scope are unchanged.


Component outcome: 42 admission/publication checks pass on actual 0.3/0.4 recording
copies. The current browser verifies comparison and generic installed-provider
acknowledgement guards at both widths without new admission; its initial POST
acknowledgement and foreign-child response are explicitly labelled transport fixtures
over an actual retained operation. Two real new children fail CARLA readiness,
retain partial canonical journals and release their owned resources. A responsive
private authenticated display removes the X11 prerequisite, but the diagnostic
CARLA process then waits at the NVIDIA modeset device; root cause remains unproven.
No host desktop/driver changes were made. T091 remains open pending successful full
native rerun and its remaining comparison/replay acceptance audit. See
`evidence/studio/M4-installed-frozen-reruns/`.
