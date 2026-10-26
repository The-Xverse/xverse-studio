# Profile conflict, security and architecture checks (T063)

**What was run.** On the T062 candidate, after the repairs below:
- the profile conflict and security contract cases: `test_profiles.py` and
  `test_profile_presentation.py`, covering namespace collisions, core-semantic redefinition, malicious
  presentation, unsupported versions, tampered and duplicate locks, unsafe presentation characters and
  markup, and mixed domains;
- `test_review_regressions.py`;
- `test_connections.py`;
- the strengthened `scripts/check_architecture.py` with its tests.

Result: 92 tests pass, and the architecture check passes.

**Strengthened boundaries** (`scripts/check_architecture.py`, run in every `run_checks`):
- **Domain dispatch.** A domain literal is caught in any comparison, conditional expression, loop or
  assert test, comprehension filter or `match` case. Domain names in declarative data are still
  allowed. Matching now includes hyphenated namespaces (e.g. `process-control`), which the old token
  split missed.
- **Dependency direction.**
  - The foundational packages (`storage`, `security`, `evidence`, `events`, `xdl`) never import feature
    packages.
  - Only `api` and `host` import the API layer.
  - `xdl` may use the assertion and scenario-authoring helpers it validates.
  - The current graph is in `dependency-graph.json`.
- **Browser hooks.** `dangerouslySetInnerHTML`, `innerHTML`, `new Function(` and `eval(` are rejected
  in `apps/studio-web/src`.

**Findings in the inspected candidate** (a1f9139), all detected by the new check (red-checked against
the committed sources) and repaired:

| Finding | Repair |
| --- | --- |
| `xdl/examples.py` chose the domain profile with `... if identifier == "reference-automotive" else ...`, a domain conditional in a core module | The domain profile is a data field of each owned blueprint |
| `xdl/__init__.py` imported `xverse_studio.profiles` (foundational → feature) | The pinned domain identities live with the owned blueprints in `xdl/examples`; `profiles` imports them from there |
| `catalog` imported the strict request base from the API layer | `Body` lives in `security/models.py`; `api.models` and `catalog` import it from there |

**Audit hardening.** An independent audit found the current code clean but the check bypassable. The
following were added, one regression test each (39 architecture tests):
- Relative imports (`from ..profiles import x`, `from .. import profiles`) and
  `importlib.import_module("xverse_studio.*")` are resolved to their packages.
- Domain literals used to select behaviour are dispatch: subscripts (`handlers["automotive"]`),
  `get`/`getattr`/`hasattr`/`startswith`/`endswith`/`pop`/`setdefault` arguments, and dict keys. Only
  the owned blueprint data module `xdl/examples.py` may key data by domain.
- The browser scan also rejects `outerHTML`, `insertAdjacentHTML`, `document.write`, `srcdoc`,
  `javascript:` URLs, bare `Function(` and string `setTimeout`/`setInterval`. It now covers
  `index.html` as well.
- `exchange` and `integrations` are classified as feature packages.
- `assertions` and `experiments` are a documented exemption for `xdl` only. They are XDL semantic
  helpers, and they form a known `xdl` ↔ helper import cycle. No other foundational package may
  import them.

The T062 review's request to re-check the sanitizer is met. Presentation is refused as a whole on
markup, scripts, or control, zero-width, bidirectional and BOM characters, as well as on unknown terms
or icons and non-https/urn references. Presentation never reaches semantics, plans or execution.

Native Windows is blocked at user request.
