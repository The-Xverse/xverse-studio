# Full-browser findings before repair

The first combined candidate run retained under `full-before/` passed 35 checks and failed three,
with product/test source unchanged throughout. It is not a successful final cohort.

- BROWSER-R01: neutral authoring's keyboard fixture focuses Create immediately after opening the
  authenticated workspace, without waiting for its busy-disabled state to clear. The final failure
  screenshot retains the project-name input focus and an unsubmitted dialog. A controlled startup
  read is being used to distinguish a missing test precondition from a product failure.
- BROWSER-R02: the unknown-lifecycle recorded fixture received an exact 1,015-record presentation
  gap, while its assertion required an unknown count. Source review identifies a separate transport
  boundary mismatch: the backend reserves 200 data frames plus one control, while the parser caps
  all coalesced frames at 200. Network chunking can therefore turn the same known gap into a parser
  error with unknown loss. This requires protocol alignment and a deterministic boundary regression;
  genuine unknown-count coverage must remain intact.
- BROWSER-R03: the actual full keyboard journey failed to restore focus to Preflight after Escape.
  The modal already supplies an explicit restore selector; its unmount/ref cleanup needs a concrete
  reproduction and repair. The focus expectation must not be removed or replaced with a mouse click.

The actual native replay-window-expiry test passed in this failing full run. That success does not
erase the three failures or substitute for the full successor checks.

Repair evidence:

- R01's controlled actual startup-read hold showed Create disabled, focus remaining in the input,
  zero POSTs on Enter, then exactly one created project after enabled/focused Enter. The helper
  now asserts those prerequisites before keyboard activation; no acceptance expectation or timeout
  was relaxed. See `../M2-neutral-assets/keyboard-create-precondition/` from the Studio evidence root.
- R02's deterministic parser case failed on the allowed coalesced 200-data-plus-control batch.
  The successor admits that batch in either order while separately rejecting 201 data frames and
  two controls. The unknown-lifecycle browser fixture now requires its exact known omission count;
  the separate genuine unknown-loss case remains. See `reserved-control-slot/` and the explicit
  `unknown-fixture-scope-erratum.md`.
- R03 was reproduced in native Chromium with earliest post-mount Escape. Synchronous New handled
  it, but asynchronous Preflight left the event unprevented and dialog open. Listener installation
  now uses the layout phase; existing topmost-dialog checks, focus restoration and keyboard journey
  assertions remain. See `../M1-modal-keyboard/before/`. This is evidence of late passive listener
  installation, not an assumed mutable-ref cleanup defect.

The final source build/typecheck passed. Focused and full successor browser receipts are recorded
separately when complete; these repair descriptions alone do not make the failing cohort pass.
