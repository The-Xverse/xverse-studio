# Installed recovery implementation and evidence review

Outcome: installed Linux recovery and current host-verification reporting pass the
scoped checks. T039/T098 remain in progress; no task status or milestone changes.
This is a separate same-agent audit, not independent milestone acceptance.

The package is built from a clean detached candidate worktree. All 177 committed
payloads and six tested compiled assets bind exactly to the archive and extracted
installation; no source checkout supplies backend modules or explicit UI paths.
Provisioning uses the pinned offline cache. All final 529 source inputs match Git
and remain stable throughout the installed/native/browser stage.

Source review limits product changes to descriptive host claims in capabilities,
the package manifest and compatibility register. Existing provider OS declarations,
security, runtime lifecycle, file acquisition and recovery implementations are
unchanged. Current supplied Linux-and-Windows engineering rules take precedence
over historical ADR-0036 scope omissions. Windows remains unverified, with its
original failed checkout and known native file-primitives gap retained. Required
native targets never imply verified provider support or successful installation.

The real completed Autoverse recording is reused only in copied roots. Actual
installed HTTP, CLI and browser operations verify static discovery, ownership
refusals, restart, full backup, restoration, corrupted input, non-overwrite and
explicit known-schema copy migration. Original and copied metadata/receipts and
project/snapshot/journal/import files were compared separately after shutdown.
Original backend identities and root locks were checked directly. The source
recording and original enrolled assets remain unchanged.

Two development failures belong to the new harness, not application defects.
It first assumed restart must expire a valid session, contrary to the existing
contract, then tried reopening an already authenticated httpx client. Corrected
checks preserve normal-session behavior, independently require restore invalidation,
and close the client explicitly. Both attempts remain recorded. The older package's
OUT_OF_SCOPE_ADR0036 field genuinely conflicts with the currently supplied rules;
successor metadata and actual Environment/API/package checks repair that claim.

No finding remains in the scoped tested behavior. Native Windows, clean-host/network
provisioning, full launcher/failure/release matrix, independent review and wider
acceptance are not established. The controlled schema0 header is explicitly labelled
and does not substitute for an actual released-version upgrade. No new simulation,
physical authority or successful T091 rerun is claimed.
