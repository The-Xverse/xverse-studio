# Actual follow verifier boundary finding

The approved native experiment2e0373e7 reached running and passed actual driving/
cruise. The controller then failed its live-phase assertion because the response
array can include an initial oldest-first request whose body arrives after the
Follow checkbox is enabled. Response arrival alone is not a request-start boundary.
The signed cleanup request was issued by the original browser controller; retain
this failed attempt and its original evidence.

Repair the verifier to retain each request's explicit order and distinguish initial
oldest/pinned reads from fresh newest requests. Require at least3 fresh newest
captures, at least2 changing source witnesses, advancing original ordinals and
allowlisted native scalar observations. Assert every counted response matches its
newest request and run identity. Do not filter on response order alone, which could
hide a server ignoring the requested order. Product follow code remains unchanged.
