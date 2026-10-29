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

Retention uses explicit run IDs, project IDs or artifact registration IDs. Preview a dry-run plan,
inspect exact scopes, dependency edges, protected IDs and expiry, then explicitly apply that plan's
fingerprint. No host path, URI or glob is a deletion target. The admitted rule is `explicit`; there is
no background age-based cleanup. A request selects at most 128 IDs.

- Run-file retention removes owned journal/process files while keeping lifecycle/result records and
  immutable snapshots. Evidence becomes unavailable, rather than successful. Active/unknown runs,
  evaluations, live annotations and campaign references can protect the evidence.
- Project retention removes an unreferenced managed project tree and its current index entry. **Any
  historical snapshot/run/campaign dependency protects the project**, including snapshots created by
  preflight. It never cascades into snapshots or evidence. A project that has been used may therefore
  remain protected until a separately admitted dependency-retention workflow exists.
- Artifact retention removes catalog registration metadata only. It never fetches, follows or deletes
  the registered origin URI, external file or simulator/device artifact. Matching declared IDs,
  digests and origins in project locks/source/snapshots/imported evidence protect shared registrations.

The backend bounds its proof scan to 10,000 dependency records per collection, 20,000 inspected files,
64 MiB inspected bytes and 4,096 reported dependency edges. Malformed/unavailable dependencies,
unsupported source/supporting formats, unsafe links and exceeded proof bounds refuse a plan rather
than treating a truncated scan as proof of independence. External filesystem drift makes apply stale.

Apply rechecks dependencies and source proofs, persists intent before effects and records each outcome.
Project retirement stages its owned tree, commits the index/tombstone/audit transaction, then purges.
An uncommitted failure restores known staged bytes; a genuinely committed retirement is never reversed.
Partial purge reports remaining managed files. Preview/apply the same explicit project ID again to
inspect and remove eligible residue; this cannot select an arbitrary staging path. Interrupted applies
remain unknown and are never blindly replayed. Retention history and tombstones preserve the audit.

Broad campaign/snapshot/index garbage collection is not supplied. Canonical evidence and historical
assessment verdicts are never rewritten by deleting files or registration metadata.

Stop Studio before full backup/removal and follow [recovery](recovery.md). Portable project/evidence
exchange does not include an offline Python wheelhouse. First provisioning and cross-OS exchange need
separate evidence; native Windows and bidirectional transport remain unverified until their lane runs.
