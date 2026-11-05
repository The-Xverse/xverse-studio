# Campaign child-input focus and retained lab inventory keyboard checks

Source `cc459ab4c131884b637015b5a16f7acf8ef8687e` passes8 campaign and36 inventory
browser checks at1024×768 and1440×900. All568 selected source inputs match Git
and remain identical across both final cohorts. Six UI assets stay unchanged and
reproduce exactly in a second build. Typecheck, targeted helper lint, architecture
and planning checks pass; build warnings remain retained.

All six initial campaign journeys fail after verified child inputs become visible:
the heading cannot receive focus, and the child-read completion path targets the
generic error heading. With an older history error still present, successful child
inspection can focus that unrelated error. The repair adds a focusable child-input
heading to the existing guarded completion routing. No input, result or authority
semantics change. Two additional delayed actual-response controls pass on the
original UI and on the repair, preserving focus after the user moves elsewhere.

The three original test templates, expanded over both viewports, are byte-identical
after the repair. Their source was reconstructed from retained Playwright failure
contexts and matched against the original captured source hash; the presentation
adds one extra final newline, which was removed before matching. AST comparison
verifies the unchanged callbacks. The only test-helper extension makes Enter
optional for the two additional focus-movement controls; existing calls keep the
same default. All eight final callbacks also match the pre-repair control source.

Campaign journeys use native Tab/Enter to inspect actual retained history and two
immutable child inputs, check text status/provenance and selected heading contrast,
recover from one labelled503 history reply, refuse one labelled post-read child-key
mismatch, retry the actual response and preserve newer keyboard focus. Fresh
planning remains explicitly unavailable without a ready preflight. This suite
registers no external provider and creates no preflight, snapshot or campaign.
The existing positive planning suite keeps its provider receipt requirement and
one-preflight/one-snapshot expectations; it is not replaced by this read-only suite.

The existing36 inventory journeys exercise actual empty inventory and clearly
labelled HTTP/display projections: Unicode bounds, missing physical declarations,
unknown/partial observations, labelled limits, native refresh/paging, actual retry,
stale response isolation, focus, labels, selected contrast and viewport bounds.
Every journey checks zero mutative requests and unchanged actual asset/project/run
lists. These observations grant no physical, reservation or probe authority.

Original recording/database bytes, copied canonical run/snapshot bytes and execution
ledger counts remain unchanged. Original backend/browser handles exit, roots release
and all17/45 captured descendant pidfds exit, with zero capture races. No GPU
descriptor is observed in readable capture-time samples. Short-lived descendants
may be missed; this is not a general GPU-health guarantee. Browser-only CPU/minimal-
device isolation is verified and is not an application prerequisite. Original
Autoverse runtime infrastructure stays shut down; no workload is started.

The public derivatives replace operator/tool/workspace paths and loopback origins,
and normalize trailing whitespace. Raw failures, contexts and screenshots remain
private. Forty source/derivative hashes and eight private session-string exclusions
are checked. See [verification](verification.json), [review](review.md) and
[remaining coverage](coverage.json).

Counts remain72 completed /18 in progress /10 blocked, zero accepted milestones.
T038/T097 stay open. These44 checks do not establish the complete reservation/probe,
assessment, export, fresh campaign-operation or actual assistive-technology matrix,
required Windows support, successor performance/package or milestone acceptance.
Windows remains separately frozen; the full goal remains active.
