# Scenario authoring returns keyboard focus after removal

Source `cc981c0e0e9a91d3affa522af853f1ce992a5b28` passes28 native Linux
Chromium checks:8 new authoring journeys,6 existing diagnosis journeys and14
existing evidence-import journeys. Each suite covers1024×768 and1440×900.
All565 selected source inputs match Git and remain unchanged across the three
final cohorts. Six UI assets remain identical and reproduce exactly in a second
production build. Typecheck, targeted helper lint, architecture and planning checks
pass; existing build warnings remain in the retained output.

The first authoring cohort passes2 conditions journeys and fails6 deletion
journeys. Successful deletion removes the dialog's original Remove button. Focus
then falls out of the authoring controls. The repair gives that dialog an optional
fallback to the corresponding Add control when the original opener is disconnected.
Escape and rejected removal continue to restore the existing Remove button.
The same eight test bodies/assertions pass after the repair; no failure is rewritten.

The new journeys use native Tab/Enter/Space, keyboard text entry and select keys.
They check visible focus and viewport bounds for reached controls; conditions and
stimulus validation; preserved opaque values; stimulus source/edit navigation;
observer/metric references and atomic rejection of referenced-observer removal;
opaque fault intent without a provider capability; modal Escape and successful
deletion focus. Selected conditions-error text contrast is measured at both sizes.
Existing suites retain diagnostic recovery/newer-focus and evidence-import
navigation/selection behavior after the shared dialog change.

The ordinary native backend operates on private copies of actual completed
Autoverse recordings. No live Autoverse provider, model, campaign or evaluation is
started. Original database/recording bytes, copied canonical evidence and execution
ledger counts remain unchanged. Authoring changes only the copy's project draft;
the14-case import suite retains12 inert imports. Original backend/browser handles
exit and workspace locks release. The diagnosis/import drivers also verify exit of
15/23 captured original descendant pidfds; this is not complete short-lived process
coverage. Browser-only CPU/minimal-device isolation is verified. No GPU descriptor
is observed in the readable capture-time samples; no general GPU-health claim follows.

The initial contributor runner accepted a relative output directory, placing its
browser report and failure artifacts under the test configuration directory. The
runner now resolves its explicit paths before launch; the initial originals remain
at their original locations. Derived public files replace operator/workspace/tool
paths and loopback origins; raw originals and six failure contexts/screenshots stay
private. See the hash-bearing retention manifest and source/UI input manifests.

Counts remain72 completed /18 in progress /10 blocked, zero accepted milestones.
T038/T097 remain open. This component does not establish the complete lab/campaign/
export matrix, actual assistive-technology operation, full regression, successor
performance/package acceptance or required Windows support. Windows stays frozen;
the full goal remains active. See [review](review.md) and [verification](verification.json).
