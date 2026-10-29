# Physical-provider contract fixtures

Synthetic identities and metadata exercise the existing backend lab contracts without contacting
hardware. `physical: true` describes the binding under test; `evidenceScope: fixture` prevents an
admission claim. The double is loaded only by tests and is never registered in the application.

The inventory contains one identified asset and one unresolved asset, with observed and unknown
firmware/metadata. A controlled clock and call journal expose exclusivity, expiry, renewal,
acknowledgement loss, disconnection and release/stop uncertainty. No endpoint, credential, executable,
driver or physical action is supplied. Test grants authorize only in-memory calls.

These fixtures support T070. AC-021/022/023 still require an actual nominated device/provider,
permission and retained physical observations; fixture results cannot pass those live cases.
