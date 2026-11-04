# Linux recorded playback verified with browser devices isolated

The current verification task is finished: **22 of 22 browser checks pass** at
1024×768 and 1440×900 on candidate
`ad8133460d7b43a77c71779368cee560a80c79e9`. The entire original playback specification
is byte-identical. Its native helper retains all five original assertions.
All 550 selected code/tool/config inputs match committed Git and stay unchanged
through verification; six prior UI build assets are unchanged. No new build occurs.

The ordinary Linux backend runs on the host. Only its browser test process uses
the optional contributor isolation: a minimal `/dev`, private `/tmp` and `/run`,
disconnected desktop/session-bus variables and disabled GPU acceleration/rasterization.
Actual setup verifies a different mount namespace, the minimal device list, absent
display sockets and required launch flags before allowing browser startup. The
actual browser argv also contains both disable flags. A controlled unisolated
setup is refused before any browser is launched. Missing/unverified isolation has
no permissive fallback.

This isolation is explicit test tooling, not a Studio installation/runtime
requirement or an admitted provider environment. Existing system bubblewrap0.6.1
is used without installation, privilege escalation, desktop/driver changes or a
simulator. It is not a general security sandbox claim for hostile browser code.
The browser's GPU device nodes are absent and sampled descriptors show no GPU
file handles; this does not assert a particular software GL implementation or
hardware rendering/performance envelope.

The unchanged checks cover all 21 actual original Autoverse receipt payloads,
keyboard playback/paging, exact returned records, absent source-clock timestamps,
read failures, bounded display, integrity/context/shape refusals and late-response
focus. Controlled transport and decoded-response fixtures retain their labels.
No source data gains numeric clock alignment, new measurements or determinism.

Original/copy canonical bytes and run/operation/evaluation/idempotency counts stay
unchanged. The original backend exits and the copied root lock releases. All31
observed original process handles report exit. No failed capture attempts are
recorded; sampling does not establish coverage of every short-lived child.
No model/provider/simulator/physical workload is started. The existing complete
T088 recording is reused without registering its provider.

The earlier interrupted cohort remains in
`evidence/studio/M1-native-root-ownership-20261104/`: zero passes,11 failures and11
skips. The user subsequently rebooted and confirmed the display working. The
underlying graphics-stall cause is not established; the successful current cohort
does not rewrite that failure or establish a driver repair. This cohort uses a
separately recorded device/rendering policy. No NVIDIA timeout is observed in the
kernel journal during the current cohort; no broader hardware-health claim follows.

Production sources are unchanged from the root-ownership candidate. No Windows
source or Windows-specific test changes/runs occur. **All Windows-related work is
frozen until explicit user lift** under ADR-0069. After retaining this current task,
**all work pauses until the user explicitly resumes**; a general resume leaves
the independent Windows hold active.

This is selected Linux read-only browser evidence. No fresh complete simulator
rerun, package, performance, whole regression, Windows or full acceptance pass is
claimed. T091 and broader gates remain open. **Counts remain71 completed /19 in
progress /10 blocked; zero accepted milestones. No additional task closes.**

See [verification](verification.json), [cases](browser-cases.json),
[commands](commands.json) and [ledger audit](ledger-audit.json). Raw process
identities, full browser reports and screenshots remain private.

Tooling references: [bubblewrap0.6.1 namespace/device options](https://github.com/containers/bubblewrap/blob/v0.6.1/bwrap.xml)
and [Chromium rasterization switch](https://github.com/chromium/chromium/blob/main/gpu/config/gpu_switches.cc).
