# Independent evidence query review, findings before repair

Scope: read-only review of root-owned query/reader/history/observations code, using isolated synthetic Linux fixtures with process creation forbidden. No live provider, Windows, equipment or original source corruption is claimed. Product/tests/tracker files are not changed by this reviewer.

## EVID-Q-I01 — malformed expected-digest metadata causes an untyped HTTP 500 (MEDIUM)

Confirmed before repair in `probes.py` and `before-repair.json`, with stable source hashes: query cbad50fd, reader 6316563e, app 20e464c5 (full hashes retained in JSON). A correct immutable one-record journal is supplied with malformed run metadata `journalDigest: []`. The reader inserts this unhashable value into its cache key before validation, so direct acquisition raises TypeError; GET history returns 500 INTERNAL_ERROR rather than a metadata-integrity/unavailability diagnostic. Original journal bytes remain unchanged, and no process is created.

Validate cache-dependent metadata types before cache lookup. Keep a missing expected digest distinguishable from an explicitly malformed value; do not silently turn a malformed list/false/zero into absent proof and upgrade integrity. This finding is about malformed run metadata, not evidence byte corruption or concurrent append.

The same current-source probe positively confirms the bounded 128-descriptor gap behavior and legacy observation clock inference in the presence of a malformed other-clock timestamp. Those two concerns were repaired before this recorded probe and are not reported as outstanding findings.

## EVID-Q-I02 — duplicate canonical event IDs overwrite receipt presentation (MEDIUM)

Confirmed before repair by `identity_probes.py` / `identities-before-repair.json` on reader SHA6aa3a24d and query SHAcbad50fd, unchanged during the probe. Two hash-consistent records share an eventId but have distinct sequences and receipt dates. The reader returns both with integrity valid; history returns the two original receipt values but only one presentation entry keyed by that ID, so the first record is presented with the second record's UTC receipt time. This violates stable unique event identity and truthful receipt presentation. Original file bytes are unchanged. It is a synthetic producer-metadata conflict, not reproduced byte corruption or a live provider result.

Reject/diagnose conflicting duplicate identities before returning them as a valid canonical sequence, or otherwise preserve per-record presentation without a collision. At-least-once transport delivery does not justify assigning distinct canonical records the same stable event ID.

## EVID-Q-I03 — malformed sequence representations are accepted through int coercion (MEDIUM)

The same stable-source identity probe confirms `sequence: true`, `sequence: 1.5`, and strings `01`, `+1`, and whitespace-padded `1` are accepted as the first valid sequence. The versioned envelope requires a decimal integer string safely encoded across languages. Int coercion silently converts malformed metadata, including a fractional sequence, into the expected position. Preserve the canonical field contract and report the malformed invariant explicitly; do not rewrite original sequence bytes. Existing owned worker and performance fixtures already encode canonical `str(index+1)` sequences.
