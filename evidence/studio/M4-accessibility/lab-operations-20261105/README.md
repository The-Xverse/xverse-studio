# Lab software fixtures serve the selected UI and preserve keyboard operation

Source `48cee68c114fddb4d586d4b768feb49c4f2b7983` passes84 native Linux browser
checks in five selected files:82 unchanged reservation/probe/recovery cases and
two new native field-entry journeys. No failure, skip or flaky outcome occurs.
All570 selected source inputs match Git and remain unchanged throughout the run.
All84 fixture hosts serve the same six selected UI files, verified by504 HTTP file
hash checks. The assets match the previously reproduced cc459ab build; production
and build inputs remain identical to that candidate. No new build is inferred.

The fixture hosts previously selected their UI only through a hardcoded dist path.
They now accept an optional trusted contributor build path, with the original
default preserved. Shared fixtures pass the explicit path and verify actual served
bytes before each journey. Initial Lab navigation now uses native Tab/Enter. The
four original spec files and all their test bodies remain unchanged; their original
interaction methods remain in the failure cases. This is not a replacement of
those cases with weaker checks or a claim that every legacy interaction uses Tab.

The two new journeys use native Tab, select keys, text entry and Enter for the full
authenticated reserve/renew/release flow at1024×768 and1440×900. They verify labelled
scope and duration fields, visible focus/bounds, selected label contrast, rejected
zero duration without a mutative request,60-second acquisition and90-second renewal,
preserved reservation/fencing identities, explicit release and unchanged empty
project/run lists. Physical-state uncertainty remains visible.

The existing cases exercise actual HTTP/API routes over owned in-memory callbacks:
independent scope grants, denied/stale authority, lease expiry and renewal, lost
acknowledgements and exact-key retry, bounded history, restart reconciliation,
unknown/refused outcomes, probe clocks/private fields, malformed replies, storage
failure, delayed responses and preservation of newer focus/navigation. The host
shutdown witnesses retain their explicit no-equipment scope. There are40 lease-host
and44 observation-host witnesses across12 fixed scenarios.

All84 hosts retain shutdown witnesses, and all175 captured original process handles exit. The
driver observes zero capture races, unavailable capture-time descriptor reads or GPU
descriptors, and needs no additional descendant cleanup. Short-lived processes can
still be missed. Fixture helpers retain their original bounded termination policy;
this is not universal graceful-shutdown or GPU-health acceptance. Browser/fixture
backends use optional contributor CPU/minimal-device isolation, not an application
prerequisite. No model, run snapshot, campaign or evaluation is created in any of
the84 fixture workspaces. No actual equipment or runtime integration is admitted.

Sixty-six witnesses retain zero in-memory leases and18 retain one, as required by
the owned/unknown/uncertain test scenarios. Process exit does not turn those stored
states into verified releases or physical safety. See [witness summary](witness-summary.json).

Current targeted lint, typecheck, architecture and planning checks pass. Per-test
120-second, fixture15/60-second preparation and10-second teardown budgets remain
unchanged. A1200-second bound was declared for this new whole batch; it completed
in202.7 seconds. This is a contributor execution bound, not a product SLA.

Public derivatives replace operator/tool/workspace paths and loopback origins and
normalize trailing whitespace. All252 retained bootstrap/session credential values
are absent,84 private credential markers have owner-only permissions and private
callback sentinels remain absent. Raw workspaces/credentials stay private. See
[candidate binding](candidate-binding.json), [review](review.md) and
[remaining coverage](coverage.json).

Counts remain72 completed /18 in progress /10 blocked; zero accepted milestones.
T038/T097 remain open for the full workflow/accessibility/required-host matrix.
Actual hardware, full binding/substitution, assessment/export and fresh campaign
keyboard acceptance remain separate. Windows stays frozen; the full goal stays active.
