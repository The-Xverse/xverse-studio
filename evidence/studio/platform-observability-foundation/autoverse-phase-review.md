# Autoverse per-binding adapter review

2026-10-29. Separate primary-agent implementation review, not independent milestone
acceptance or a live Autoverse result. Public runtime registration remains absent.

1. The first public-service adapter case failed before dispatch with
   `AUTOVERSE-RUNTIME-INPUT-MISMATCH`. The persisted snapshot sorts document keys;
   the new runtime compared tuple iteration order. Inspection of the retained
   original inputs proved equal named source bytes and frozen configuration but
   unequal iteration order. Required repair: compare the complete name-to-byte
   mapping, preserving every original body and expected platform digest. Do not
   regenerate documents or discard unknown executable fields to pass admission.
   Original XML, log and private source data are retained. The repaired actual-service
   case passes, including rejection of changed source body bytes. A fresh scoped
   suite passes all 196 checks on candidate `73de5cfe93bafcdfb3a65d7153b4b3156afd6d04`
   without failures, errors or skips. The first 195-pass/one-failure suite remains
   retained with its original outcome.
2. Boot polling launches owned adb helpers. Such a callback cannot be a pure
   `ready` phase whose acquisition is omitted from rollback. The graph now uses
   an acquiring `android-boot-start`, followed by APK acquisition and a separate
   container liveness observation. No functional Android success is inferred.
3. Ownership observation can fail after Popen succeeds. The worker now retains
   the original child and phase association before that observation. Missing
   birth/argv evidence stays unknown; it does not authorize a signal. Separate
   tests use actual owned children for failed storage, mismatched birth, phase
   isolation, expired deadlines and partial acquisition. Test fixture teardown
   is distinct from a claimed runtime cleanup outcome.

Still required: production worker supervision and cancellation, actual installation
revalidation at the runtime boundary, native C++ payload forwarding and observation
collection, coherent bounded Argus browser projections, linked views and actual
Autoverse live acceptance. Existing Studio journal events remain Studio records.
