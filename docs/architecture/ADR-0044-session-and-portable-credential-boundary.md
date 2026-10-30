# ADR-0044: Native session and portable credential boundaries

Status: implemented;317 target API/native CLI and8 native browser checks pass,
with complete installed Autoverse confirmation and12 live invalid-caller refusals.
T010 remains open for its complete security review; no wider authority is granted.

Actual enrolled Autoverse tests reproduce non-ASCII CSRF server errors, acceptance
of non-finite native session expiry, credential persistence/export and sensitive
validation-path echo. The original122-case phase has106 failures/16 passes;
the22 additional native-state/opaque-request cases have18 failures/4 passes.
Several typed UTF-8 scalar cases already reject correctly and remain controls.
Retain these distinctions rather than claiming every source suspicion was a bug.

The native session record retains its existing two-field shape (`csrfToken`,
`expiresAt`). Missing, unsupported, non-finite, expired or unencodable records
refuse authentication without repairing/deleting persisted bytes. Opaque CSRF
comparison uses exact UTF-8 bytes with the existing constant-time primitive;
malformed/nonmatching headers return403. Successful login still consumes one
bootstrap and creates an HttpOnly/SameSite=Strict session. No remote/multi-user
authorization or new token-delivery API is introduced.

All strict request bodies inspect their complete decoded JSON for finite UTF-8
values, including opaque dictionaries and keys, before resource lookup/effects.
They preserve otherwise valid values and existing field/schema/version rules.
The existing input JsonObject and command-specific checks retain their scopes.
API refusals use the same no-store, content/security and request-ID headers as
ordinary responses, including early authentication/origin/version rejection.

Portable text screening additionally recognizes session/bootstrap/CSRF/refresh/ID
token assignments and Basic/Bearer authorization headers. A single bounded scan
decodes JSON string literals for security recognition, including quoted escaped
keys and URI user-info. Original text is retained exactly; this scan neither
validates a model nor replaces authoritative XDL semantics. Existing private-key,
GitHub marker, ordinary credential assignment and URI checks remain. External
credentialRef/sessionTokenRef handles stay valid and convey no execution authority.
The short idToken name has an explicit boundary so ordinary names such as
gridToken remain exact. A separately reproduced interim false positive and its
repair are retained; existing credential assignment checks are not weakened.
Project names and layout metadata receive the same ordinary-content screening;
portable export screens historical content without rewriting original records.

Validation diagnostics retain ordinary schema locations but replace sensitive,
unencodable or oversized components with an explicit redacted marker. Components
are bounded to256 characters and complete paths to1024; the existing20-diagnostic
cap remains. Raw input values and credential/private-path strings are withheld.

Verification targets enrolled Autoverse classic/platform authoring/import/export,
native browser rendering/cookie/refusal cases, and invalid callers against actual
running demo controls/Stop. This alone does not close bounded exchange/metadata
read review, the full T010/lifecycle matrix, or external/human/milestone gates.

Final source confirmation passes317 API/native CLI checks and8 native browser
checks on435 unchanged inputs plus6 UI assets. Clean candidate90d6a45 package167
matches161 committed payloads,6 tested UI assets and canonical SDK12615d402. Its
complete native demo verifies12 invalid-caller input/Stop refusals with no mailbox,
command, lifecycle or denied-idempotency effects, then completes original owned
Stop and same-key retry. All16 original processes are absent,3 exact containers
stopped,root lock released and21 original platform files unchanged. This confirms
the scoped boundary, not all remaining T010 or milestone requirements.
