# Exchange projects and recorded evidence

Use **Import project** on the workspace home screen to select a local ZIP. Import
creates a new project envelope; authored XDL identities and supported semantic
content remain unchanged. It does not fetch dependencies or install providers.
Review **Dependencies**, validate the imported source and request a new preflight
before execution. A missing integration or unresolved host binding blocks Start.

Use the project's **Export** control for its exact current revision. The portable
package contains its manifest, sources, declared profile sidecars, layout and
artifact lock. It excludes run evidence, private local bindings, sessions and
credentials. Declared missing or restricted artifact references remain references;
export does not copy their external payloads or override distribution restrictions.

In **Results → Evidence**, **Export evidence bundle** packages the selected run's
verified frozen snapshot, captured original journal, source report, recorded
evaluations and annotation history. The manifest hashes every included member.
`report.json` retains source evidence scope/status and identifies referenced
runtime/compiler/profile/artifact payloads that are not included. Those identity
pins do not establish availability or permission on another host.

Select **Import evidence** on the home screen to inspect a local evidence ZIP.
**Current inspection** shows the result of this import's checks. **Original report**
preserves the producer's reported integrity, evidence status and scope separately.
A damaged journal stays invalid even if its provider reader is unavailable. An
intact unsupported source remains unavailable for that reader; recorded data does
not become a new executable run or an admitted device/Argus source. Original
assertion/metric results remain source records and are not reevaluated by import.

Expand a dependency identity or the retained metadata using keyboard or pointer.
Dependency payloads are not fetched or installed. A report without a supported
dependency summary explicitly says it is unavailable. Internal digest consistency
is not producer authentication or a reproducibility guarantee.

New portable exports must fit the existing import request allowance: 6 MiB minus
1 KiB for the current 8 MiB base64 JSON request. Expanded content remains bounded
to 16 MiB, with per-document, entry and compression limits. An oversized export
is refused before a download operation is published. Retain the original data
and select a smaller project or run; Studio does not truncate historical evidence.
Unsafe names/links, incompatible versions, inline credentials and host-only content
are refused rather than silently rewritten.

Local bindings stay private. Their files cannot be smuggled into a portable
archive. Moving a complete private workspace requires reviewing its declarations
on the new root/host; that move does not change portable model identity or grant
execution authority. Native Windows and provider support have separate verification
requirements; an imported package does not establish them.
