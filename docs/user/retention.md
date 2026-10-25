# Retention and evidence exchange

Project ZIP exports contain explicit authored XDL, manifest, pinned references and presentation
sidecars. They exclude native sessions, owner secrets, arbitrary host files and run directories.
An import allocates a new project envelope identity while preserving XDL identities; missing or
unsupported dependencies remain visible and cannot be installed or executed by import.

An evidence export binds the exact source snapshot/compiled plan, original reference journal,
reader integrity and availability, evaluations, revisioned annotations and trace links. An evidence
import verifies the archive and internal identities in an isolated managed location. It remains
**imported recorded evidence** with `executionAllowed=false`; a valid internal digest does not confer
provider authority, prove producer authenticity or establish simulator/device admission.

Canonical journal bytes and snapshots are immutable. Comments, trace links, metrics and reports are
separate derived records. A link to a requirement never proves that requirement passed. Annotation
updates/deletes require revision checks and retain history/tombstones.

The current deletion scope is explicit run-file retention. Request a dry-run plan, inspect protected
active inputs and dependencies, then explicitly apply the same unexpired fingerprint. The backend
rechecks state, persists intent before filesystem effects and records per-item outcomes. A stale plan
rejects; an interrupted operation is unknown and never blindly replayed. Partial deletion is reported.
Original lifecycle/result records and source snapshots remain; current evidence availability becomes
unavailable when files are removed. Shared dependencies, annotations, evaluations and campaigns can
protect referenced run evidence. Broad project/artifact/campaign garbage collection is not yet supplied.

Stop Studio before full backup/removal and follow [recovery](recovery.md). Portable project/evidence
exchange does not include an offline Python wheelhouse. First provisioning and cross-OS exchange need
separate evidence; native Windows and bidirectional transport remain unverified until their lane runs.
