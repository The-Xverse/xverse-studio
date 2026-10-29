# Implementation review: read-only inventory presentation

Root source review of the independent read-only portion of T075; this is not an
independent agent review or acceptance of M3. No new agents were delegated.

The original suspicion needed qualification: “No physical provider admitted” is a
true, separate current backend admission fact. The reproduced defects are omission
of inventory completeness/provider diagnostics and use of obsolete firmwareVersion.
The initial four actual failures are limited to those assertions. The successful
backend preservation/no-write assertions ran after their soft UI failures.

The existing LabView export is preserved through OperationsViews.tsx. The new feature
module consumes ADR0018's public projection, separates admission from observation,
and keeps unavailable reservation integration explicit. Existing reservation response
UI/handlers are retained, while current public admission/readiness fields cannot
enable them. Backend authority checks and refusal paths are unchanged.

Response validation bounds rows, known scalar/record/diagnostic fields, cursor progress
and page positions. It checks the current public shape and does not reinterpret XDL
or confer execution authority. Unknown extras are excluded from raw inspection;
identity/revision strings remain inert. Metadata truncation and unknown declarations
stay visible rather than promoted to successful observations.

Only a single client read is active. Refresh and page reads abort their predecessor;
departure invalidates the generation and aborts browser observation. This does not
claim that cancelling fetch stops a provider's trusted inventory method. A client
deadline becomes an explicit unknown result. Local errors cannot leak through a
captured global doAction continuation. Explicit current completion receives focus
only while origin/BODY and modal guards permit; initial navigation focus is retained.

Pages are separate current observations, never merged into a frozen inventory. Failed
page rows are removed and explicit refresh restarts at page one. The backend's actual
default100-row paging was mirrored by labelled100+1 UI transport observations. Thirty
initial successor journeys passed; review added cursor-cycle refusal and stronger
positive metadata/scope/readiness checks before the final32 freeze. No app bytes changed
for those test additions or ADR amendment. Final candidate gates establish their own
results. Native Windows, actual AT, reservation integration and live-device acceptance
remain open; this review cannot establish those requirements.

Physical-declaration follow-up: source review found that project_asset normalizes a missing raw physical property to false. The first UI incorrectly inferred a non-physical realization from that flag. Root deliberately interrupted the first full run (188 passes/101 not run, exit130), retained it without a full-pass claim, then generated the omitted-property projection and executed two actual failing native witnesses. The corrected Physical declaration row says Not confirmed physical for false and Declared physical asset for true, preserving canonical realization separately. The corrected source was rebuilt before final34/full291/performance gates. Original fixture bytes were reconstructed and SHA-verified against the initial map; the added fixture leaves original payloads unchanged.

Unicode follow-up: the next complete 34/full291/performance 2 cohort passed and is preserved as before-unicode evidence. A real backend projection accepted 256 Unicode code points in model and firmware fields, represented by 512 UTF16 code units; the client string.length check incorrectly rejected the valid observation. Two actual native red witnesses preceded a code-point count with a bounded UTF16 precheck. Corrected final 36 passes both viewports, exact Unicode display, zero writes and no horizontal overflow. A fresh full 293/performance 2 pipeline is required for the new compiled candidate; earlier 34/full291 is not labelled the final current cohort.
