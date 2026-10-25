# Recorded replay / fresh rerun implementation record

Date: 2026-10-25. This is implementation verification, not independent milestone acceptance.

The initial focused suite was red because the rerun module did not yet exist. After implementation
and root route installation, all **eight cases passed in 48.21 seconds**. They use actual owned
reference executions plus explicitly identified failure fixtures:

- Recorded observations/history/evidence reads create no Run or snapshot.
- An explicit rerun creates one new child Run and snapshot with the same authoritative plan and exact
  original execution source bytes, despite a changed editable draft. Original journal/snapshot/evaluation
  bytes remain unchanged; duplicate outer keys retain the same operation and child.
- Snapshot file or database-digest tamper blocks child creation. Changed current plans/providers reject.
- Invalid old observation evidence is retained as invalid; separately verified original inputs may
  produce fresh new observations without repairing old evidence.
- Lost child acknowledgement resolves the durable child-start mapping without a second start.
  Restart with no proven dispatch remains unknown and does not replay Start.
- A real imported evidence bundle has no Run ownership; a public frozen-override field rejects.

ADR-0003 records the ownership, freshness, lineage and result semantics. Frozen profile-lock checking
and source Run/project/revision binding were subsequently tightened; final affected verification and
candidate source hashes are retained separately. Native Windows and external/physical reruns remain
unavailable/unverified, and an outer completed operation means child creation rather than experiment
completion or an assertion pass.
