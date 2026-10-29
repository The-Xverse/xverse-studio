# Studio recovery integration review, before repair

Reviewed the uncommitted successor of691a19d after accepted SDK12615d402 admission.
Read-only pass; the fixes below were not applied during this pass.

- R01: Owner-history creation fsyncs the file but not its directory. Before replacing
  the diagnostic marker, persist the historical directory entry as well.
- R02: Public Core constructor failures while recognizing receipts currently escape
  as ExecutionInputError. Translate refusal to Studio's actionable recovery-required
  installation diagnostic, while retaining the fence and closing any opened service.
- R03: Two conformance fixtures need correction: the synthetic predecessor directory
  must have the real SDK's private mode, and the public live-root refusal code is
  MPX-RUNTIME-ROOT-BUSY. Expanded result13passed/2failed reflects these exact gaps;
  it is not a passing result. Initial result8passed/1failed used an incomplete marker.

The real owned-child recovery/new-run, unchanged source, idempotence, corrupt receipt,
changed claim, changed installation and unaccounted marker-run cases pass. The64
affected preparation/execution/XDL/Argus/views checks pass. Native bridge was rebuilt
against the actual accepted platform source and produced the prior binary digest.
These are scoped checks, not the complete live demo acceptance.

Next repair and repeat affected checks before retiring the original registration.
