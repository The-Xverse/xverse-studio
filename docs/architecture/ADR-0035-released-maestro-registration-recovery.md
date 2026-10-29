# ADR-0035: Recovery of a verifiably released Maestro registration

Status: proposed scope; no companion implementation or platform acceptance implied.

## Concrete prerequisite

ADR-0034's actual GUI attempts left a durable claim in the existing isolated
simulation registration after the original Core worker exited. The first run was
cancelled through its original signed host channel. The original public SDK
reported `MPX-START-CANCELLED` and released cleanup; independent inspection found
its nine original process receipts absent and two acquired containers stopped.
The subsequent Core correctly refused activation with
`MPX-ORIGINAL-OWNERSHIP-UNAVAILABLE`. Original claim/evidence files remain intact.

Studio's persistent backend owner fixes sequential operation while ownership is
retained. It cannot recover an already lost public Core instance, convert a PID
into an original handle, or remove the predecessor claim. An admitted public
recovery capability is a prerequisite to executing again in that registration.
Read-only historical views and independent Studio work can continue.

## Narrow proposed companion scope

Separately scoped work in `xverse-platform` would specify, implement, test and
review the following public capability against the accepted public execution
baseline. The platform chooses actual public names and types; this document does
not invent an existing callable API.

1. Inspect whether a selected host registration's predecessor claims are eligible
   for retirement, using the actual original claim and public Argus reader. Bind
   each claim's run, compiled plan, authored-input, operation and correlation
   identities, root identity and source witness. Return explicit refusal reasons.
2. Permit retirement only when original, closed and structurally verified lifecycle
   evidence accounts for every attempted acquisition with released cleanup and a
   terminal stopped/failed outcome. Unknown cleanup, missing lifecycle facts,
   corruption, an open writer or changing source remains ineligible. Incomplete
   native observation sampling is a separate dimension; it cannot conceal missing
   lifecycle provenance or manufacture a complete trace.
3. Require an explicit host-owned, finite and digest-bound recovery permit for the
   exact inspected registration/claims/source witnesses and installed provider.
   Imported XDL, browser fields, caller-invented records and PID lists grant no
   recovery or process-control authority.
4. Retain original claims and Argus bytes unchanged. Record retirement separately,
   durably and idempotently, with its original provenance and permit binding. New
   activation in the same registration may recognize only a verified retirement
   record. A stale/changed source or any remaining unresolved claim still fences
   activation. Retirement does not recreate old resource handles or relabel an old
   unknown read snapshot as observed release.
5. Inspect/retire without signalling a process, modifying a container, stimulating
   a device, or replaying Start. Serialize with the actual public root owner and
   refuse a busy/live registration. Partial writes and restart must fail closed.
6. Verify identity/source/permit mismatches, corrupt/missing/truncated lifecycle
   evidence, cleanup uncertainty, writer-open/source-race cases, concurrent owners,
   duplicate retries and interrupted retirement. Exercise actual owned-child runs
   and original Argus, retain the existing public SDK/native regressions, and then
   verify the approved simulation on its existing registration. Fixtures alone do
   not establish the complete Autoverse/browser result.
7. Follow the companion repository's specification, implementation, evidence and
   review rules. Platform acceptance remains the user's. Do not replace Studio's
   admitted dependency or integrate a candidate into platform main before its
   required acceptance and exact-candidate verification.

Excluded: physical/hybrid or new OS support, forced cleanup, arbitrary root reset,
claim deletion, recovery from unknown/corrupt evidence, private entry points,
publication and cloud deployment.

## Authority and Studio impact

Studio `AGENTS.md` states: “Cross-repository changes require separately scoped work
under that repository's rules.” The accepted boundary at `ce2d5558...` intentionally
has no released-claim retirement operation. This proposal is additional companion
scope; the previous acceptance is preserved. Until separately authorized and
admitted, the existing registration stays fenced. The end-to-end goal and its live
acceptance cases remain open, with existing task IDs and milestone states unchanged.
