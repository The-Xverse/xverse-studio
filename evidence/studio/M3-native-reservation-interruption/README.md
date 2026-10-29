# Native reservation interruption boundaries

The fresh focused cohort passes **107 tests**, including the two volatile-provider
restart cases and three new in-flight native backend crash cases. All 319 selected
source/configuration inputs match before and after this final cohort. The existing
159 backend/fixture/lock inputs still match published af45890; no application
source changes are required by this supplement. There is no fresh full 1073-test
backend run. The concurrent full 516-case browser and performance checks have
their own controller and outcomes.

The native fixture host retains the real application routes, authentication,
Origin/CSRF checks, operation identities, transactions and provider callbacks.
Test-only wrappers pause timing at fixed boundaries without changing the values
passed to the original storage/provider methods. The controller verifies the
durable operation and lease through a read-only SQLite connection before killing
only its exact owned child, guarded by UID, parent, argv and process birth.

| Boundary | Durable state at crash | Normal restart and explicit inspection |
|---|---|---|
| Before delegation | One accepted operation; no lease or provider effect | Original operation becomes unknown; no invented lease or acquisition |
| After provider effect, before acknowledgement | Delegated operation; unknown lease without a recorded fence; one fixture effect | Inspection cannot invent/adopt the unrecorded fence; ownership remains unknown |
| Before final operation receipt | Delegated operation; confirmed lease with its original fence; one fixture effect | Lease first restores unknown; explicit matching owner/scope/fence inspection restores owned state |

Every original-key retry returns the same original operation and reservation
identity without replay. Even after explicit ownership reconciliation, the original
interrupted operation receipt remains unknown rather than being rewritten as a
successful historical acknowledgement. Unknown ownership rejects renewal.
Restarted provider observations contain no reserve, renew, release or stop calls;
their fixture effect files remain byte-identical. No run is created and physical
runtime admission stays unavailable.

Provider continuity is **simulated by an owned durable JSON fixture effect**. It
is not evidence of a surviving external provider, device, driver or safe physical
cleanup. The timing hook intentionally stops real backend execution at a declared
point; it does not establish an arbitrary crash distribution or actual hardware
failure rate. The killed host cannot produce its normal shutdown observation.
The restarted host's real observation is required and retained separately.

The first three-case and first 107-case successes remain historical. The latter
had an input observation made after completion despite its initial label; that
qualification is preserved. The final 107-case controller records actual inputs
before and after execution and is the binding result. All reports are text;
raw bootstrap/session state, databases and screenshots stay private.

T073/T074 remain in progress: reservation scope grants do not substitute for
physical-command API observation/stimulation/destructive-action conformance.
Automatic active-run renewal, ownership-loss/stop integration, actual permitted
hardware/provider/clock/cleanup evidence, held Windows and complete independent
milestone acceptance remain open.
