# ADR-0060 — Preserve private enrollment across native backend restart

Date: 2026-11-04. Status: implementation and verification in progress.

The real campaign restart case retained its original running worker, but normal
launcher startup tried to enroll its busy installation again. Cold enrollment
correctly requires stopped containers. Startup therefore installed an unavailable
provider, losing compatible input callbacks and preventing later child admission.
The failed case, exact owner witnesses and verified cleanup remain retained.

Persist a server-generated classic installation receipt in a bounded owner-only
file in the private Studio data root after successful cold enrollment. A later
startup with the same explicitly selected root reads the protected receipt and
rechecks immutable files, SDK versions, container identities and artifact pins.
It does not adopt a new baseline or re-enroll changed assets. Missing receipts use
ordinary stopped-environment enrollment; malformed, unsafe, mismatched or changed
receipts expose an unavailable provider with a typed reason.

Identity verification is distinct from execution readiness. Reconstructing the
same installed adapter does not acquire resources, open control ports, admit a new
Start, or bypass a running worker's installation lock. Existing full readiness and
worker verification remain unchanged and still reject occupied containers, ports,
unrecognized scratch and incompatible source. Active input requires the original
owned run/snapshot and current matching provider descriptor. Cleanup authority
remains with original owners.

The receipt is host-local private data, never project/profile/import metadata or
portable execution authority. The normal launcher root lock excludes concurrent
writers. Read/write uses native safe managed I/O, finite size, regular-file/owner/
mode checks and complete receipt integrity. Reusing a data root on another host
requires explicit local provider repair rather than automatic identity replacement.
Platform enrollment remains a separate capability and is not admitted by this fix.

Verify unsafe/malformed/changed receipt refusal without re-enrollment first, then
repeat actual native backend crash/restart with the original worker, driver lease,
immutable child snapshots and no duplicate dispatch. Tasks and milestones remain
open pending their complete evidence; native Windows remains unverified.
