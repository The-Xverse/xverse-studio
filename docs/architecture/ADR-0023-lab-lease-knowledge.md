# ADR-0023 — Preserve terminal lease facts and uncertain reservation intent

Status: registry repair under verification; positive HTTP reservation authority and
physical-provider admission remain separate work.

Date: 2026-10-27.

T073/T074, FR-049/FR-050 and AC-022/AC-023 require fenced ownership, durable intent
before delegation, truthful uncertainty and repeated release that cannot affect a
newer owner. The registry-only fixture review reproduced three defects before
implementing durable HTTP reservation backing:

- Restoring a confirmed released or expired record replaced its terminal status
  with unknown, losing known history and preventing idempotent completion.
- A provider's typed uncertain reservation error discarded the already persisted
  intent even after the fixture had acquired the lease.
- Authority already known to be uncertain still contacted provider inventory,
  which could obscure the ownership failure with a separate availability error.

Preserve confirmed `released` and `expired` records on restoration. Restore every
nonterminal record as unknown until the provider confirms the same owner, fence,
scope and unexpired deadline. Terminal records confer no authority and neither
release nor reconciliation contacts their provider. Expiration is not undone by
restoring the record.

Treat `RESOURCE_BUSY` as the existing provider contract's definite refusal before
allocating a lease. Preserve its existing rejection behavior. A typed exception
alone proves no such refusal: every other provider reservation exception retains
the durable unknown intent, with no invented fence and no repeated acquisition.
The caller receives `OWNERSHIP_UNCERTAIN`. Errors raised by registry admission
before delegation keep their existing codes and perform no provider reservation.

Check ownership status before consulting inventory for an authority request. An
unknown or terminal record refuses authority without contacting the provider,
regardless of later grants or declared capabilities. Existing owner, scope,
capability, fencing and renewal checks remain authoritative for owned records.

Verification appends six registry-only cases covering terminal restoration with a
newer owner's lease, typed uncertainty after actual fixture acquisition, denial
without inventory contact and a definite-busy control. Existing registry and
physical-contract cases remain. Serialized fixture records and provider call
counts establish the scope; no equipment is scanned or contacted.

The shipped application still has empty provider inventory and refuses unadmitted
reservation mutations. This repair adds no provider installation, HTTP action,
permission grant, device/driver, physical stimulation or native Windows acceptance.
It is a prerequisite for the planned durable backend authority work, not physical
integration or task/milestone completion.
