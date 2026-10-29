# Native bridge implementation review

2026-10-29. Primary-agent source/failure review, not independent milestone or
complete Autoverse acceptance. Runtime registration and the three views remain open.

- The first network attempt rejected the newly built executable because the
  contributor umask produced a group-writable file. Original mode, configuration,
  logs and failing outcome are retained privately. The host build procedure must
  create a private build directory and normalize its own new executable to 0755.
  Do not relax runtime checks or chmod an unrelated installed production binary.
- Public native submit/receive and original observation accessors work. The first
  C++ builds failed warning-as-error checks for ambiguous Json-to-optional
  conversion; explicit optional construction repairs these without suppressing
  warnings. The logs retain the original build failures.
- Successful isolated network proof uses two owned ephemeral loopback routers.
  It proves bidirectional bytes pass the bridge, actual native coalescing, and no
  forwarding after closure. It does not start CARLA, Android or the complete demo.
- The first native contract suite passed 11 checks and failed an assertion that
  indexed optional `causationId` on every Argus record. Actual import, native
  coalescing and the incomplete verdict had already passed; the initial annotation
  correctly omitted an unknown cause. Repair the assertion to preserve absence,
  without changing production records. Original failed Argus data/XML are retained.
- Shutdown needs an explicit callback admission cutoff under the same lock used
  to admit frames. Relying on subscriber undeclaration alone leaves uncertainty
  about callbacks already executing. Stop must drain every frame accepted before
  the cutoff or report a bounded failure, then close native routes. Verification
  of the repair and actual original Argus imports is pending.

Retain native provider counters separately from Python ingress bounds and public
Zenoh put receipts. Downstream application consumption and simulator time remain
unknown. A coalesced native sample is not a complete traffic trace.

Reviewed successor: `81aaf797f0defee04b34f7e8ad94f05926175eb9`. The callback
cutoff repair is implemented; final actual network verification checks native
child exit independently and confirms no forwarding after bridge shutdown. Twelve
explicit native contract cases pass, including actual Argus import with original
coalescing counters and an incomplete verdict. The affected suite passed 142
cases on `7bc933b`; the successor removes two terminal blank lines only, then
rebuilds to a byte-identical executable and repeats native contracts/network proof.
All original failures remain retained. No full demo, runtime registration, linked
view or milestone acceptance is inferred.
