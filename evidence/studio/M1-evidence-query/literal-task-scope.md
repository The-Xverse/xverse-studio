# Literal T028–T030 task scope audit

Read-only audit on 2026-10-25 against tasks.md, FR-017/018/020/021/022, AC-010/011, run-events.md, and the current reader/query/API/UI/tests. No product or test source was edited, no test/browser/provider was run, and no tracker state was changed for this audit. Root reports the focused 62-case backend successor green; the keyboard-green author receipt records six browser cases passing in 33.7 seconds. The current full backend cohort was still in progress at audit time. These outcomes are not new execution evidence from this reviewer.

| Task | Recommendation | Literal scope assessment |
| --- | --- | --- |
| T028 | Keep open for the remaining explicit fixture obligations. | Read-only recorded fixtures now cover original-source preservation, valid/invalid integrity, declared gaps, mixed clocks, exact signed ticks above 2^53, missing versus measured zero/false, corrupt metadata, bounded pages, and delayed/stale UI read responses. The independent successor probes also cover a live append acquisition refusal followed by a stable verified-prefix retry. However, the reviewed tests/fixtures do not yet contain a protected/redacted-field or private-log-exclusion fixture demonstrating the admitted reader's restriction boundary. They also do not exercise an advancing producer with a genuinely slow UI consumer and an explicit stream.gap/retrieval outcome. A delayed HTTP response tests stale-read isolation, not that transport gap obligation. |
| T029 | Complete the implemented owned-evidence reader/query component. | The admitted owned-reference journal is acquired through the bounded managed reader; unavailable/invalid/verified-prefix states remain distinct. Unique envelope IDs/canonical sequences and the hash chain are checked without rewriting original bytes. Versioned bounded filtering, pre-page predicates, context-bound cursors, quality/facets/gaps, exact clock/receipt handling, original scope, and raw metadata preservation are implemented and covered. No private provider stream is opened. This is not an Argus reader admission claim: no external reader is substituted or presented as tested. Remaining T026 stream expiry/resync and T028's specific fixture coverage must stay visible separately. |
| T030 | Complete the implemented Results presentation component; retain the T026 dependency as outstanding lifecycle/transport work. | Selected-element logs/events/observations, emitter/observer/severity/source-clock/receipt-time predicates, stable evidence/model navigation, exact source ticks, raw receipt inspection, clock/quality/integrity markers, explicit collection/display omissions, and bounded 200-row rendering are present. Request context/abort/generation guards prevent old run/filter pages from appearing as current; local evidence selection does not navigate away. Different quantity units/resolutions use exact tables without inferred alignment. Missing time never becomes zero or an array index. Six native cases cover the focused slice, including keyboard overflow, incompatible metadata fallback and delayed retained-to-live transition. This does not establish T026 retention-expired cursor resynchronization or the AC-010 fast-producer/slow-browser full matrix. |

The remaining software obligations are concrete: add the restriction/redaction/private-log-boundary fixture and the producer/slow-consumer explicit delivery-gap fixture, and implement/verify T026's expired-cursor resynchronization. They are not unavailable-Windows or missing-hardware excuses. Native Windows work remains held at the user's request and broader AC-010/011/M1 acceptance remains independently open; those do not erase the usable owned reader/query/presentation implementation. No requirement or acceptance criterion is waived.

## Reviewed source identities

- evidence/reader.py: `d8be82d6adf8fd8ba353a97730f0f1afc1fa25556a7790934b67b6b8f1bab2f2`
- evidence/query.py: `0df0c6508892deea08d277749fd2c6ec50b9a82df58b4b2c4b01a0a5e6df897a`
- api/app.py: `7b556fbb21bbd76e9beb150469da82289fe8ae221b30f68defd5cd72a7c4d796`
- test_evidence_filters.py: `d984dcd98024a0454b803de169c4b7dcbc0e20a53e722a23550051d71f1f5c31`
- test_evidence_projection.py: `256336a1128197dcbde10eabc032a7d220c4d942a089a4bbdcab5a259b73285e`
- fixtures/evidence/create_recorded_evidence.py: `8849a7ed76e7cf125f8fc0e6d1390057b17476f8416d68dc8b296bc315f3231b`
- evidence-filters.spec.ts: `5ffccb28df2cf7e6993eb1c70a0e1394902ea3d4ff4479e609a13ab74496d2ea`
- ResultsView.tsx: `92f13dac5b75d6e6881fd264962369ca2a1ec94d5c31ebc724c6cc036d592e63`
- ObservationDisplay.tsx: `19a4fae4cbfc75bd818df753d6e888bf1263707a8698730290b63807ca84aca6`

See the independent successor review for the closed reader metadata/identity findings and exact semantics probe receipts, and M1-evidence-filters/independent-frontend-review.md for the read-only frontend review and keyboard successor amendment.
