# Physical provider admission

Status: BLOCKED for actual hardware acceptance (T071/T080, AC-021–AC-024).

No actual device/provider identity, supported driver/firmware combination, permitted
nonhazardous actions, reservation implementation, clock contract, laboratory
location or device-specific authority has been supplied for this implementation.
The Studio implementation authorization does not supply permission to access,
stimulate, flash or modify an arbitrary attached device. No equipment was scanned
or contacted. No companion repository was modified.

The shipped laboratory registry starts with no providers and an empty inventory.
Providers must be explicitly admitted backend-side; project metadata cannot install
or execute one. A provider must supply bounded inventory, reserve/renew/inspect/release
operations, unique fencing identities, explicit action capabilities and scope,
lease deadlines, metadata/readiness observations and disconnect/stop policy.
Stimulation and destructive authority are independently checked and are denied by
default. A reservation does not grant authority beyond its declared scope.

The owned tests exercise a portable in-memory fixture only: exclusivity, concurrent
claims, observe-only defaults, denied stimulation, renewal, expiry, stale fencing,
unknown restart ownership, idempotent release and uncertain/failed stop. They are
labelled fixture evidence and establish no physical integration. Missing stop or
clock evidence remains unknown; browser disconnection does not become a device-stop
observation.

To unblock hardware acceptance, nominate an exact device/provider revision, serial
or equivalent immutable observed identity, driver/firmware and OS/architecture,
explicit approved test environment/actions, provider reservation/clock/stop contract,
and practical device access. Verify each advertised OS separately. Linux-only
provider support cannot establish Windows device support; the native Studio core
has a separate support/evidence matrix.
