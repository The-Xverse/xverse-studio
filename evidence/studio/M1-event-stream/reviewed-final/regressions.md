# Permanent regressions after independent findings

The original independent findings and first 16-case receipt are retained. Six additional permanent cases passed, followed by the unified 22-case cohort on identical before/after source hashes.

Two cases invoke the actual API endpoint and its ASGI response with a send function that fails during http.response.start, once by OSError and once by cancellation. Each observes one admitted lease before response startup, zero leases immediately after failure, no body delivery, and zero leases after closing the never-entered iterator. Original fixture journal bytes remain unchanged.

Four correctly rehashed disposable journals contain an LF event kind, CR event kind, unregistered kind, or reserved transport-control kind. The independent canonical reader and JSON history still report valid cryptographic evidence and preserve the exact original kind. The event transport responds with typed 422 STREAM_ENVELOPE_UNSUPPORTED and integrity=valid, rather than interpolating unsupported text into an SSE header or rewriting the journal. This specifically verifies the transport admission boundary and does not tighten the broader cryptographic reader contract by stealth.

No product code, reader contract, private/slow-consumer fixture behavior or original completed-stream regression was changed by this test author. Windows work remains held; these disposable Linux tests make no external provider/device claim.
