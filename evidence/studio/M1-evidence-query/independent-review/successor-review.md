# Independent evidence query successor review

Final reviewed hashes: query `0df0c6508892deea08d277749fd2c6ec50b9a82df58b4b2c4b01a0a5e6df897a`, reader `d8be82d6adf8fd8ba353a97730f0f1afc1fa25556a7790934b67b6b8f1bab2f2`, app `7b556fbb21bbd76e9beb150469da82289fe8ae221b30f68defd5cd72a7c4d796`. All independent successor probe source-before/source-after hashes match. This reviewer changed only review scripts/receipts, not product code, tests or trackers.

## Recorded findings closed

- EVID-Q-I01: malformed declared digest metadata returns invalid integrity, including through HTTP 200 evidence inspection; no untyped 500 occurs. Missing expected proof remains distinct from malformed proof. The correct original journal bytes are unchanged.
- EVID-Q-I02: conflicting duplicate event IDs stop the valid prefix and mark integrity invalid. The retained first event keeps its own receipt presentation; it is no longer overwritten by the second event's timestamp.
- EVID-Q-I03: bool, fractional and noncanonical sequence representations are refused as invalid envelope metadata, with no rewriting of original bytes.

The three original findings and before-repair JSON remain preserved. None is a claim that byte corruption or live device behavior was reproduced.

## Additional independently verified semantics

`semantics-successor.json` records successful assertions for exact source tick 9007199254740993 and half-open selection; explicit zero/false/null versus absent/malformed source time; epoch receipt zero versus false and unknown numeric codecs; original-decimal receipt filtering; paging after selection; cross-run/filter/route cursor refusals; bounded facets with explicit incompleteness; raw input preservation; and no invented generic tick unit from reported resolution. The known reference tick unit requires the admitted reference context; raw resolutions remain separate metadata and mapping remains null.

Six malformed HTTP selections each returned a typed 422 rather than 500. A synthetic recorded-fixture run keeps its recorded scope rather than becoming owned-reference execution evidence. The source bytes remain unchanged through these reads.

A controlled append of a valid next journal record during acquisition returns unavailable, not invalid corruption. The original prefix is retained, and a stable retry reads both valid records as verified_prefix. This fixture append is intentional producer activity in a disposable file, not a modification of pre-existing evidence. Gap descriptors remain within the advertised 128 bound, and legacy single-valid-clock inference ignores malformed other-clock timestamps while preserving their quality counts.

Receipts: `digest-successor-complete.json`, `identities-successor.json`, `semantics-successor.json`. Root's final 62-test cohort and the separately reviewed UI/browser cohort are author evidence; their counts are not added to these independent probe assertions.

No further concrete issue was found in the assigned query/reader/history/observation scope on these hashes. Recommend closing this scoped independent review and proceeding to root's exact full-candidate checks. This does not close M1 or native Windows/external-provider/hardware acceptance. No process was launched, external reference fetched or equipment operated by these probes.
