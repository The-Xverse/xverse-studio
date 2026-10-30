# ADR-0050 — Autoverse journal-opening refusal

Date: 2026-10-30. Status: implementation candidate; verification pending.

## Problem

The actual enrolled classic Autoverse worker creates its journal before entering
the normal execution/finalization handler. Exclusive-create failure exits without
a state report. Two native reproductions, for an existing directory and regular
file, leave the accepted Start with unknown lifecycle and cleanup. Neither case
acquires demo resources or reaches effective-input validation.

## Decision

The initial journal opening catches only `OSError`, closes the unused selector,
and reuses the existing provider-neutral diagnostic in an owner-bound failed report with
`reason=evidenceFailure=EVIDENCE_OPEN_FAILED`, complete cleanup with no
acquired resources, unavailable native evidence and the actual terminal time. No
started/effective-plan, journal digest, event count or canonical failure event is
invented. Exclusive creation remains unchanged and preserves an existing object.

Only a successfully published report produces the closed opening-failure result.
If report publication fails too, that error propagates and backend ownership stays
unconfirmed. The classic entry point exits unsuccessfully after the typed refusal.
The normal execution and finalization paths remain authoritative.

The read-only evidence reader is unchanged. A pre-existing invalid object remains
invalid in the API even though the worker reports that it could not create its own
journal. Failed Start, cleanup, native evidence availability and reader integrity
remain separate facts. Subclasses retain their existing owner-aware save method;
this does not grant new Maestro, X-COM or Argus authority or rewrite prior evidence.

## Verification and scope

Use explicit trusted native-host fault choices immediately before the fixed
server-owned Autoverse worker launch. Project/profile/imported metadata cannot
select a fault or command. Retain original 202/retry identities, actual native
failure reports, unchanged frozen inputs and journal objects, absent workload
resources, original process exits and root-lock release. Repeat the complete
nominal demo as the positive guard on the changed implementation.

This is T033 progress in the actual Autoverse integration lane, alongside the
original owned-fixture matrix. It does not replace that matrix, resolve its earlier
late-Stop mismatch, close T033, or establish full acceptance. Existing task IDs,
requirements, acceptance cases, authority and public major versions stay unchanged.
