# Evidence read-projection findings before repair

Baseline product commit 180d026 (published documentation head de395ff), native Linux. These are
source-confirmed findings unless a separately retained dynamic receipt explicitly says otherwise.
Windows installation/testing remains on user hold. No external device/provider or private stream
is operated by this work.

- EQ-001: history accepts only kind/severity/element selection. New source/time query parameters
  are silently ignored by the previous route; there is no emitter/time predicate before pagination.
- EQ-002: observation projection converts missing source tick to zero and always labels output as
  simulation-time/microsecond with an invented reference mapping. Mixed, missing and malformed clocks
  cannot be distinguished through this projection. Original record hashes remain independent of it.
- EQ-003: reference recordedAt is Unix seconds, but Results constructs Date directly from the numeric
  value as milliseconds. Receipt time and source time require declared, independent interpretation.
- EQ-004: observation requests lack run/filter generation guards, and plotting substitutes array
  position for absent time and converts original tick strings to Number. This can invent coordinates
  or lose adjacent ticks beyond JavaScript's exact integer range.
- EQ-005: the owned journal reader checks a pathname size before an ordinary unbounded read_bytes.
  Source inspection establishes a bounded-acquisition gap; no disclosure, race success or excessive
  allocation is claimed from this finding alone. The replacement must admit files through anchored,
  bounded acquisition and treat concurrent append/change honestly without altering canonical bytes.

Repairs add evidenceQuery 1.0, exact signed integer half-open source selection, independently decoded
UTC receipt selection, actual whole-run bounded facets, filter-before-page behavior, explicit unknown
quality/collection gaps, cursor context checks and browser request isolation. They grant no new runtime
capability, physical mapping, evidence integrity or assertion verdict. T026 retention expiry/resync and
native/live milestone gates remain separately open.
