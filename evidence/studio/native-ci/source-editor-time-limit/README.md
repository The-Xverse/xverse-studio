# Source-editor predecessor CI time limits

All four native Ubuntu24 jobs ended cancelled at the configured 25-minute total job limit.
Primary GitHub annotations identify the exact limit. Retained browser-step logs reach
161/170/162/165 passing cases with no assertion-failure lines before cancellation. There
is no completed browser cohort, and package/smoke stages were skipped. Uploading partial
artifacts does not change those cancelled outcomes.

Run/job IDs and all step conclusions remain in the adjacent 7ec222b/a950572 run receipts.
These are distinct from the locally passing 171-check/native-package evidence and from
new recovery-panel 209 checks. Full raw job downloads remain private/local; the retained
browser step includes its command/progress/cancellation, with GitHub workspace paths
normalized. Check-run annotations were read through the authenticated GitHub API via gh
because the connector did not support that read route.
