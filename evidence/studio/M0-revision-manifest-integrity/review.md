# T008 revision envelope integrity repair

This is progress within the existing T008 storage component. Its dependency IDs,
FR-001/NFR-009 and AC-002 remain. T008 is not complete: generic private local
binding sidecars, their CAS publication/export exclusion and moved-root review
still need implementation and conformance. No milestone is accepted here.

| Reviewed boundary | Repair and verification |
| --- | --- |
| Reopen actual revision files | Compare project.studio.json with the manifest already sealed for that source revision through the bounded secure managed reader. Changed, reformatted, malformed, missing, unsafe, oversize and nontext files are visible. Diagnostics retain observed facts and digests without echoing external content. |
| Existing layout and older data | Layout-only updates compare against the sealed source manifest, so the current presentation metadata is independent. Older metadata lacking a textual history seal compares canonical non-layout fields with durable metadata; it gains no invented historical byte provenance. |
| No new current-draft work from a mismatch | Compilation, preflight, semantic source save, export and a Start following an earlier ready preflight refuse before new work allocation or launch. Snapshot existence from the earlier preflight is retained; no new run/receipt is created. |
| Explicit recovery | Existing document-adoption/recorded-restore requests preserve external readable envelope bytes as sidecars, then create a new forward revision using recorded envelope metadata. Arbitrary external manifest fields do not become resource/profile/provider authority. Original revisions remain and the private preserved endpoint returns exact observed bytes. |
| Invalid sealed history | Foreign project/revision IDs, Boolean revision, missing/malformed manifests, malformed row JSON, nonfinite values and unencodable values give an unverified observation. Restore refuses before allocation. The malformed original row and file stay unchanged. |
| Receipt/snapshot independence | A completed export's original same-key receipt/bundle remains valid after a later draft conflict; a new export refuses. A separately admitted owned reference rerun uses verified original frozen inputs while the current envelope stays conflicted, preserving the original snapshot and producing one distinct child. |
| Existing persistence and native behaviour | Project revision/conflict, explicit dependencies, unknown source, CLI plan identity, migration, secure file acquisition, real backend restart, full backup/reopen and inert path tests remain included in the final affected cohort. |
| Actual browser recovery | Four new native Chromium journeys exercise both recovery actions at1024x768 and1440x900, with keyboard activation, byte preservation, recorded metadata, validation and reopen. Six existing native source/recovery/keyboard journeys exercise readable and unreadable files at both sizes. No workload is dispatched by the browser journeys. |

Caller transactions are preserved: sealed-row reads reuse the current transaction
rather than opening another SQLite writer during Start or recovery. The repair
adds no platform API, provider/physical permit, new XDL/envelope version or hidden
file-command execution. The existing user demo is not restarted.

Original results stay separate. The first corruption phase retained10fail/1pass
plus a TestClient teardown error caused by its pytest.fail launch stub. Two new
recovery cases initially used an incorrect request schema/status; those fixture
assumptions were corrected before targeted reproduction. The corrected three-case
phase fails at the actual missing observation/admission. Initial repair31 passes,
then174 affected and10 browser cases pass. Final sealed-history review adds three
first-failing decoding/finite/UTF-8 cases; the final successor is recorded in
verification.json with its exact source map rather than relabelling prior phases.

Final successor: **187 backend cases and10 native browser cases pass**, with all412
tracked source/config/test inputs and6 compiled UI assets unchanged before/after.
The final cohort includes the earlier boundary and new malformed-history checks;
no passing total is assembled by relabelling an older candidate. T008 stays open
for its generic private binding sidecar implementation; task counts remain55/35/10
and no milestone acceptance is implied.
