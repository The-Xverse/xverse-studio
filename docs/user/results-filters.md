# Select recorded results

In Results, **Delivery view** chooses retained history or the bounded live buffer. It is separate from
**Emitter provider**, which selects the source identity actually reported by records. The live buffer
is only the browser's current window; use retained history for the complete retained selection.

Choose an **Element reference**, **Emitter provider**, **Observer**, and observation field as needed,
then apply the selection. Options come from bounded whole-run metadata, including fields beyond the
first page. An incomplete option list is labelled. Results shows at most 200 records per page and
reports matching and omitted counts. Resetting a filter resets paging; a cursor from another
selection cannot silently be reused.

**Original source clock** selects exact tick boundaries in that domain. Start is inclusive and end
exclusive. Enter signed decimal integer ticks without fractions or exponent notation. Large ticks
remain exact. No clock is mapped to another merely because its values look similar.

**Recorded receipt UTC** selects a separate backend receipt interval. Enter timestamps with an
explicit timezone, for example `2026-10-25T12:00:00Z`; at most six fractional digits are supported.
Original receipt values remain inspectable alongside their interpreted UTC display. An unknown
numeric encoding stays unavailable. Receipt time is not substituted for simulation/device time.

Unknown or malformed source time remains visible in the table and is omitted from timed plots.
Zero and false values remain measurements. Incompatible clock, resolution or value-unit metadata
uses the table instead of an inferred plot. Raw fields and provenance remain inspectable; any omitted
value columns are counted. Focus the named table region and use the arrow keys to scroll wide data.

Integrity, collection gaps, display paging and assertion verdicts are independent. A display selection
does not repair missing evidence, validate a provider, pass an assertion or start/stop a run. Switching
runs or filters discards obsolete read responses; browser cancellation affects the read only.
