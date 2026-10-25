# Studio reference preview — implementation checkpoint

Application candidate: `0dd3ea89f6b158849499d0b506b1919d05dfa953`.
Branch: `implement/studio-m0-m4`. Draft review: https://github.com/The-Xverse/xverse-studio/pull/1.
Status: runnable Linux development reference. **No M0–M4 milestone or Studio 1.0 acceptance claimed.**

The five System workflows share authoritative XDL identities. The browser can create/open/import,
compose and edit source, pin profiles, author/select deployment/scenario variants, preflight and run
the admitted owned model, reconnect, inspect immutable inputs/results, rerun frozen inputs, assess
bounded assertions/metric dependencies, execute finite campaigns, compare, annotate, exchange and
plan/apply run-file retention. Unsupported controls and unadmitted providers remain explicit.

Thirteen component tasks have cited implementation evidence: T003, T006, T013, T017, T024, T036,
T041, T042, T044, T050, T085, T086, T087. Other tasks remain unchecked/in progress or blocked in
`tasks.md` and `traceability.json`. Component completion does not waive retained acceptance gates.

## Executed verification

- Native Ubuntu 22.04.5 x86_64: **224 backend tests passed**, one dependency deprecation warning;
  captured application/test source hashes unchanged during the full run.
- Exact-candidate Chromium 156.0.8078.4: **3 browser tests passed**, no skipped/flaky/failed tests;
  includes real owned worker execution/recovery/reconnect, keyboard and both specified viewports,
  profile/variant/artifact flows, frozen-input inspection and a distinct fresh rerun after draft edits.
- Thirty measurements after one warm-up: selection p95 **32.2 ms**, open/authoritative-validation
  presentation **587.5 ms**, 50,000-event history first-page presentation **194.4 ms**. Canonical
  history identities/count/integrity stayed unchanged. Earlier failures remain recorded.
- Native Ubuntu 24.04.5 x86_64 CI: dependency installation/build, backend checks, 3 browser journeys,
  packaging and an offline fresh-extraction/native-start/persistence/public-compiler smoke passed.
- Independent M0/M1 and M2 findings were recorded before repairs. All five M2 composition findings
  passed separate Linux successor probes on the committed candidate with source hashes unchanged.

Exact environments, commands, source digests, raw outputs/samples and limitations are under
`evidence/studio/release/` and `evidence/studio/native-ci/`. These focused and full results overlap;
do not sum them. Reference evidence is not external simulator, Argus, native X-COM or device evidence.

## Windows hold and remaining gates

Initial native Windows Server 2022 Datacenter 10.0.20348 installation failed because the pinned platform
Git tree has Windows-invalid filenames. Application/browser checks were NOT_RUN. Further Windows
installation and tests are explicitly **BLOCKED at the user's request**; CI now runs Linux only.
Prepared portable-wheel work is held locally on loop10 and is not integrated into the dependency lock.

Remaining obligations include native Windows/exchange evidence when resumed, an admitted public Lite
input/plan/lifecycle contract and permitted environment, supported feedback compilation, independent
live industry providers, an identified physical provider/device/permission and actual clock/shutdown
proof, the five-person usability study, broader provider scenario/editor coverage, broader shared
artifact/project/campaign retention, and final retained release acceptance. M5 stays deferred.

## Launch and verification

After the pinned source installation and frontend build, the implementation workspace can launch directly:

```text
.venv/bin/python -I -m xverse_studio.host.launcher --data-dir .studio-local/data --port 8876
```

Open http://127.0.0.1:8876 and enter the one-use token from `.studio-local/data/bootstrap.json` locally.
No token belongs in a URL/log. Ctrl+C requests owned reference cancellation and stops the native backend;
closing the browser leaves backend-owned runs intact. Follow `docs/user/` for installation, upgrade,
backup, recovery, study protocol and retention. Provisioned core operation is local/offline.

Run `uv run python scripts/run_checks.py` and `uv run python scripts/test_browser.py --performance`
with the pinned native tools and declared local cache/temp roots. On the implementation machine all
workspace/data/cache/temp/artifact writes use the user's loop10 filesystem. Companion repositories
were read only; no physical equipment was operated or unrelated process terminated.
