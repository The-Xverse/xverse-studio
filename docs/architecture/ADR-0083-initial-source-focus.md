# ADR-0083: Apply initial source focus after the dialog renders

Date: 2026-11-06. Status: implemented candidate; component verification in progress.

Actual Chromium156/Orca42 journeys found that direct Escape from an automatically
selected source declaration restored DOM and AT-SPI focus without announcing the
return button. The installed reader's trace showed a hidden Resource-select menu
selection replacing its internal focus context after the source textarea received
focus. Its later silent context repair suppressed the returning focus utterance.
The separately passing keyboard Close button did not resolve that path.

Keep declaration lookup, source ranges, text and ordinary modal focus restoration
unchanged. Schedule only the initial automatic source anchor across two browser
animation frames so the dialog's initial render precedes its source focus. Cancel
the pending frame on effect cleanup. The callback requires the original focus to
be this dialog's Close button, that focus to remain current, the textarea to remain
connected and this dialog to remain the top modal. Newer Resource focus, a placed
caret, closing the dialog or another modal takes precedence. The explicit Go to
selected declaration action remains immediate.

This changes browser focus sequencing only. It adds no runtime scheduling,
backend, provider, permission, persistence, compiler, identity or source-edit
contract. Browser frame scheduling introduces no application dependency beyond
the browser; contributor Orca/Xvfb isolation remains optional. The speech timeout,
actual AT assertions and existing input/snapshot bounds stay unchanged.

Verify direct Escape and keyboard Close with actual Orca/AT-SPI at both required
sizes. Keep the preceding failures as historical evidence. Countercheck newer
Resource focus, a placed source caret and the earliest post-mount Escape in real
Chromium frames, explicitly labelling the instrumented countercheck input. Repeat
the existing source-only authoring journeys and bind final source/assets to the
candidate. These checks contribute to T038/T097 under AC-031; they do not replace
the full browser/AT, human, required-host or milestone gates. Windows stays frozen.
