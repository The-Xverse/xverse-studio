# ADR-0047: Provider fixture scopes and native reference admission

Status: implementation under verification for the original T011 task.

T011 requires an executable reference provider, separate fake/recorded fixtures,
controlled failure points, clock/version metadata and explicit scope labels.
The executable and closed failure host already exist, but their fixture catalogue
and recorded-run directory were missing. The reference descriptor also advertises
unverified Windows/AMD64 support despite Linux-only native I/O admission.

The reference descriptor now declares the verified Linux/x86_64 combination.
Its model/contract versions and logical behavior are unchanged. The capability
digest changes normally, so an old preflight cannot silently adopt this metadata.
Original historical descriptors/results retain their original bytes.

The native failure host exclusively creates a fresh0700 directory through the
existing anchored native API and holds the native root lock before application
initialization. Existing directories and aliases refuse before data access. It
records original worker handles, birth/argv/parent/owner facts before dispatch
acknowledgement, with absence/release independently checked after shutdown.
No application route or imported project gains a fault-control interface.

The fixture catalogue points to the existing executable and nine closed native
failure boundaries. Their logical placement is deterministic; host scheduling is
not. A synthetic provider fixture has deliberately incompatible descriptors,
its own manual clock and no native launch binding. Fake data cannot produce a
positive execution result. The recorded fixture preserves the exact portable
export from the original verified Autoverse run, including all71 journal records,
original identities/digests, absent source times and unmapped host receipt clock.
Its original external_demo claim remains distinct from current imported inspection.
Neither a recording nor a fake description creates a current run or permit.

The user explicitly approved a T011-only exception to the Autoverse test-target
instruction for execution of studio.reference. Current Autoverse checks still
verify discovery, negative fixture admission and inert recorded inspection.
The separate native reference checks execute the actual owned worker, retain
failure outcomes and compare repeated logical samples without claiming identical
host timestamps, IDs or canonical journals. Other current tasks retain Autoverse
as their verification target. This is not broader runtime/hardware admission or
milestone acceptance.
