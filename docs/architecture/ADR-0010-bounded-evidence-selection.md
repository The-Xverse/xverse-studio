# ADR-0010: Bounded evidence selection and original clock interpretation

Status: implemented owned components under successor verification; no M1 acceptance claim.

FR-017/FR-018 require source/severity/time selection without replacing unknown data with measured
zero or promoting receipt order into cross-clock causality. Previous projections inferred missing
source ticks as zero, assumed one reference mapping and interpreted Unix seconds as browser
milliseconds. History did not apply emitter/time predicates. Evidence query contract 1.0 adds closed,
bounded query models shared by native HTTP history and observation projections.

Selections compare canonical signed decimal source tick strings (at most 32 characters) with Python
integers, retain their original representation, and use half-open intervals. A source interval requires
an explicit original clock domain. Legacy observation-only intervals can resolve a single known
observation clock; mixed or unknown interpretations require selection. There is no mapping,
interpolation, source-time substitution or automatic cross-clock alignment. `resolution` is reported
metadata, not a generic unit-conversion table. Only the installed owned reference v1 clock codec
establishes its microsecond tick encoding; other unit interpretations remain unavailable.

Receipt intervals use independently decoded UTC and cannot be mixed with source intervals. RFC3339
text is decoded only within the declared calendar/precision subset (timezone required, at most six
fractional digits, no leap-second conversion). Numeric receipt timestamps are decoded as Unix seconds
only for the declared reference-v1 envelope. Other numeric encodings remain unknown. Filtering uses
the original encoded decimal seconds, not the derived microsecond UTC display. Original receipt and
source metadata remain unchanged. RFC3339's unknown local-offset notation still has a known UTC
instant; it confers no device-clock synchronization or local-zone knowledge.
See [RFC3339 section 4](https://www.rfc-editor.org/rfc/rfc3339#section-4).

All predicates apply before 200-record paging. Whole-run option facets have 64 entries per kind and
explicit incomplete discovery; original collection-gap descriptors have a total cap of 128, including
derived integrity warnings. Counts distinguish candidates, matches, returned items and page omission.
Field selection is an explicit observation-value projection; raw events retain the full immutable
payload. New opaque cursor contexts bind route, run and canonical filter. Numeric history cursors
remain accepted only for legacy kind/severity/element queries. Full retained-cursor expiry and stream
resynchronization remain T026; this contract does not claim that gate complete.

The owned journal reader uses native anchored acquisition with a before-allocation size bound and
unchanged named-file checks, including cache hits. Concurrent append/change makes that acquisition
unavailable for retry and is not proof of corruption. Missing proof remains distinct from explicit
malformed digest metadata. Duplicate canonical event IDs and noncanonical sequence representations
invalidate the stream rather than collide in receipt presentation or coerce to an expected sequence.
Original bytes and crypto digests are never rewritten. Unknown incompatible envelopes are not
silently reinterpreted. Evidence scope comes from the actual run metadata, not the reader's name.

Browser request generations and cancellation isolate both observation and history selections. Reads
cannot issue lifecycle commands. Charts retain exact integer endpoints and use bounded relative
coordinates only for comparable points; unknown/mixed resolution or value-unit interpretations stay
in the raw table. Original zero/false remain values. Table limits and hidden columns are explicit,
with raw details retained and keyboard scrolling available. All rendering is outside execution timing.

Compatibility: additive evidenceQuery 1.0 metadata and capabilities under HTTP major v1. Observation
pages now explicitly bound the prior implicit 10,000-item cap to 200 with continuation and omission
counts. XDL, assertion v1 schemas, run snapshots, profile locks, evaluator inputs and canonical journals
stay unchanged. Tests, original findings and independent successors are retained under
`evidence/studio/M1-evidence-query/` and `evidence/studio/M1-evidence-filters/`. Windows installation
and testing remain held; native secure I/O has no Windows implementation. Argus/private providers,
physical clock admission and full milestone acceptance remain separate requirements.
