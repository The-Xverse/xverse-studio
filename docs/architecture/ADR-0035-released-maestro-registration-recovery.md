# ADR-0035: Recovery of a verifiably released Maestro registration

Status: approved and implemented prototype. The user accepted reviewed platform
candidate8c2307fa9 (runtime99dc5994c) on2026-10-29 for local main and Studio SDK admission.
Assembled main12615d402 passes236 source checks,46 packaged checks and3selected
native CTests. Studio host integration is verified in scope; complete live acceptance
on the existing registration remains pending.

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
2. Permit retirement only when original, terminal-writer and structurally verified
   lifecycle evidence accounts for every attempted acquisition with released cleanup and a
   terminal stopped/failed outcome. Unknown cleanup, missing lifecycle facts,
   corruption, an open writer or changing source remains ineligible. Incomplete
   native observation sampling is a separate dimension; it cannot conceal missing
   lifecycle provenance or manufacture a complete trace. A writer terminated through
   the actual public abort path has state `failed`, not `closed`; that state alone
   is neither proof of corruption nor eligibility. Its original incomplete verdict
   must remain intact, and all identity, integrity and compensation conditions still
   apply. An interrupted phase may lack a success outcome only when its original
   acquiring intent is explicitly accounted for by released cleanup and the original
   terminal failure; absent compensation is not inferred from silence.
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
has no released-claim retirement operation. This is additional companion
scope authorized by the user after this proposal; the previous acceptance is
preserved. Until the new interface is accepted and admitted, the existing
registration stays fenced. The end-to-end goal and its live
acceptance cases remain open, with existing task IDs and milestone states unchanged.


## Retained registration inspection

Read-only inspection of the existing registration found one predecessor claim,
43 original Argus records, no public-reader diagnostics, eleven phase intents,
ten phase outcomes, nine cleanup intents and nine released cleanup outcomes. Its
original terminal event is failed with `MPX-START-CANCELLED`, cleanup released and
zero observation-transport gaps. Run/plan/input identities match the original
claim. The public abort path closes its stream and publishes a failed manifest;
its recorded and assessed evidence statuses are both incomplete. These facts
inform the proposed verifier; this inspection is not an admitted retirement proof,
recovered ownership handle, eligibility decision, or authorization to activate.
