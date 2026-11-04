# ADR-0063 — Current native-host requirements and installed recovery verification

Date: 2026-11-04. Status: verification correction implemented; native verification
in progress. Traces: T002, T039, T098; NFR-009; AC-032.

The currently supplied repository engineering instructions require native Linux
and Windows installation, startup/shutdown, browser operation, persistence, paths
and process ownership. The earlier explicit ADR-0036 Linux-only instruction remains
part of the historical plan/evidence. Apply the current instructions to new claims:
Windows is an outstanding implementation/verification requirement, not a current
out-of-scope disposition. Preserve existing IDs, dependency order, exact historical
receipts and component evidence; do not infer cross-OS acceptance from prior closure.
This amendment does not grant cloud/companion/device permissions or change stacks.

Declare both required native targets separately from recorded verified OSes. New
package manifests, capability reports and the descriptive compatibility register
report Windows NOT_RUN. The verifiedNativeOS list remains Linux. Preserve the
historical Windows dependency-checkout failure and explicit PLATFORM_IO_UNAVAILABLE
source gap. No native Windows implementation or successful installation is claimed.
Core startup must not depend implicitly on Bash, WSL, containers or a remote host.
Provider compatibility remains independently admitted per OS and installation.

Qualify the exact current installed Linux package through offline provisioning from
the prepared dependency cache, isolated module origins, every archive/extracted/
committed payload hash and previously tested UI bytes. Use the completed actual
Autoverse recording, without registering its live provider or executing another
workload. Test automatic packaged asset discovery, Unicode paths, duplicate root
ownership, live-backup refusal, restart, verified stopped backup/restore, copied
session invalidation, corrupted-backup refusal and explicit browser imports.

Normal restart preserves a valid unexpired native session; restoration invalidates
copied sessions. Keep these separate instead of inventing a restart-expiry rule.
Also exercise explicit copy migration using an actual-data copy with a controlled
known schema0 header. This is not evidence that an unidentified historical release
produced the copy. Preserve source DB/metadata/receipt/project/snapshot/journal
identities, invalidate copied sessions and require an explicit later launch.

This verifies T039/T098's installed recovery component. Broader clean-host/network
provisioning, full acceptance, Windows, performance and independent milestone gates
remain open. A prepared-cache install is not a clean-host dependency download.
