# Studio recovery integration review after repair

Read-only review of the successor recorded in recovery-review-01.md. R01 now
fsyncs the archived original marker and its directory before another owner can
replace the diagnostic marker; the injected directory-fsync failure retains the
original marker, releases the public lock and permits a verified retry. R02 maps
public constructor refusal to Studio's recovery-required diagnostic. R03 uses the
actual private directory mode and public busy-root diagnostic in the fixtures.

Verification:15 owner cases pass, followed by two affected checks including the new
durability case;64 adapter/view/XDL cases,152 other dependency-admission cases and12
actual native bridge contract cases pass. Initial failed results remain retained.
The final additional test/fixture edits do not change the tested product code.
All10 installed public execution modules match accepted platform12615d402.
The native bridge was built from that actual source revision with fresh native
libraries and matches its recorded binary digest. Compatibility, architecture,
spec structure, frontend build and affected Ruff checks pass.

No blocking finding remains in this scoped review. It is an agent review, not
independent platform acceptance. Host recovery requires an explicit existing
registration, installed provider pins and finite grant. Every predecessor marker
run must have a currently verified public receipt before a new owner is admitted;
public Start independently checks all original claims. An old read remains unknown.

Remaining acceptance: use the host tool on the original actual registration, then
complete browser Start/Stop, native Pygame driving/cruise, linked native-X-COM/Argus
views and independent resource cleanup on this same candidate. No such pass is
claimed by the fixtures or this review.
