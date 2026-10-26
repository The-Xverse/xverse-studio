# Retained full-CI regression on abd5acc

Both new viewport keyboard journeys passed in PR run 40296057424. The full cohort then failed
retention because its name-only selector matched three valid projects named Process control reference.
The added viewport projects exposed this existing shared-backend test assumption. Retention failed
before removing its artifact registration; the later composition flow then found two headings with
the same artifact name. The complete failed browser-step log is retained here, with runner checkout
paths replaced by `<repo>`.

The successor adds a stable project-ID attribute to the existing list row and scopes retention's
protected/candidate selection and removal assertion by those exact project IDs. It preserves the
valid duplicate-name setup. Final successor verification is recorded separately; the original CI
failure is never rewritten as success.
