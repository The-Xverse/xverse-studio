# Baseline — T001 Linux-only partial evidence

T001 remains open. The installed `xverse-xdl` 0.4.0 matches all five file hashes retained in
`docs/implementation/baseline.md`; `verification.json` records each expected/actual hash and the
unchanged lockfile digest. The platform revision remains
`7fab6a290c3731533c2b88517158055c768b9d4e`; no dependency was upgraded or companion repository changed.

`../M3-physical-contracts/environment.json` records Ubuntu 22.04.5 LTS x86_64, kernel, Python 3.13.13,
Node 24.22.1, package identities and application/test hashes. Actual public XDL library/CLI exercises
remain in the passing full backend cohort in that directory. Browser versions and workloads are
recorded separately with their native Linux scope.

Verification reads installed distribution files and compares SHA-256 with the existing baseline's
five table rows; `uv.lock` is hashed separately. It performs no provider launch, discovery or probe.
Windows installation/testing is held, and neither the live mutually executable compatibility set nor
unavailable normative SADS text is supplied by these Linux results. See `verification.json` for limits.
