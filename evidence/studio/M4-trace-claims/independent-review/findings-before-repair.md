# Independent Results annotation UI review, findings before repair

**Correction:** the trace-editor portion of TRACE-UI-I01 below is withdrawn. The frozen source already keys `TraceLinkEditor` by run ID. Only the review-note editor context issue remains active; see the amendment below.

Reviewed frozen ResultsView SHA f3bdbbc6c314e86df716df305dd8b559ee0ad41305798946026ade13ecfcf44e. This reviewer did not implement the UI and makes no product edits.

## TRACE-UI-I01 — annotation editor state survives a run identity change (MEDIUM)

Confirmed by source control-flow inspection before repair. `App.tsx` mounts `ResultsView` without a run key, and the frozen-input rerun callback can replace its `run` prop while remaining in Results. `TraceLinkEditor` is also mounted without a run key. Its run-dependent effect reloads subjects but preserves `open`, URI, referenced revision, reported claim, selected model IDs and selected definition IDs. If IDs are shared across the old/new runs, its payload reconstructs definition digests and the journal identifier from the **new** run. A draft external claim entered for the old run can therefore be submitted to the new run without resetting or explicitly rebinding its subjects. If an existing trace was being edited, the parent clears `editingTrace` but the child retains the content, converting it into a new-link draft.

The pre-existing review-note editor has a related target mismatch: the run-change effect clears `editingTrace` and annotation rows but does not clear `editingAnnotation` / note text. Its PUT still targets the old annotation ID after the new run is displayed.

Repair should reset annotation editor state on run identity changes and remount/reset the trace editor (for example, key it by run ID). Preserve stored historical rows; do not silently copy claims between run contexts. Verify a run switch with an open draft/edit cannot retain the old fields or update the prior run's annotation. A small component/context regression is sufficient; no external integration or equipment is required.

This is a source-confirmed UI finding; no browser reproduction is claimed in this initial record. The existing positive native browser flow does not switch run identity while an editor is open.

## Amendment after source-line recheck

The reviewer missed the existing parent JSX key in the frozen source. At `ResultsView.tsx:1030`, `<TraceLinkEditor key={run.runId}>` explicitly remounts its local state, and the next props guard `editingTrace?.runId === run.runId`. Both were already present in reviewed SHA f3bdbbc6; they were not repaired after this finding. The claim that trace drafts/definitions silently migrate between runs is therefore false and is withdrawn. No trace-editor implementation change is needed.

The narrower review-note issue remains confirmed: the run-change effect at line165 clears only `editingTrace` and rows, whereas the comment form's `editingAnnotation` and `annotation` state remain, and PUT targets `editingAnnotation.annotationId`. The same-view frozen rerun callback replaces `run` without remounting ResultsView. Reset both review-note fields on run changes and verify that an old note edit cannot update its prior run after a new run is displayed. Original observation text is retained above for review history, with this explicit correction taking precedence. This is a source-confirmed issue; no browser reproduction is claimed by this reviewer yet.

## TRACE-IO-I02 — transitive frozen-subject inspection route duplicates unsafe file acquisition (MEDIUM)

Confirmed before repair by `snapshot_io_probe.py` / `snapshot-io-before-repair.json`, with identical before/after `api/app.py` SHA ced1a33d5832a46a9b26a90f09295719014367f43484b1b39d41f1626f50f7b7. The Results subject picker calls `GET /runs/{runId}/snapshot`. That route uses `original.is_file()` and unbounded path-based `original.read_bytes()`, bypassing the new bounded anchored `Runs.verify_snapshot` helper. An instrumented hook confirms that exact unbounded reader is reached; it raises before any body allocation. No large allocation, secret read, process or hardware operation is performed, and snapshot bytes are unchanged. The controlled route fixture is synthetic metadata for a read-only request, not executed-run evidence.

This is a concrete acquisition-path violation, not a claim that memory exhaustion or outside-data disclosure was reproduced. The route returns stored metadata after comparison, so this probe does not assert disclosure. Reuse the bounded anchored verifier and retain typed missing/corrupt/oversized/symlink refusal. Root owns the route and its focused HTTP regressions; this reviewer makes no backend change.
