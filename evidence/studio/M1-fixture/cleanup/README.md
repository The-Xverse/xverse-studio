# Owned temporary-resource cleanup

This is an uncommitted successor to `af25449`. T033 remains in progress.
The final clarified source passes **1,219 backend tests, 88 affected browser
checks and two separate performance cases**, with no failures/errors/skips/flaky
outcomes in their applicable phases. All final phases use identical 380 inputs.
Clean Linux packaging is pending. [Current verification](verification.json).

The worker now attempts one release of its verified empty temporary directory.
Retained contents produce failed cleanup; replaced, missing or unobservable
identity produces unknown cleanup and no deletion. Stop/Cancel application,
model termination, resource release and evidence integrity remain independent.
The API and browser expose one bounded logical resource reference for inspection.
There is no recursive deletion or automatic cleanup retry.

The native cases verify original PID/birth/argv/owner and a real model sample
before fault delivery. They cover empty release, retained files after Stop,
Cancel and duration completion, symlink/directory replacement, a missing adopted
directory, and simultaneous cleanup/journal failure. Retained and unrelated bytes,
original snapshots and Project values remain unchanged. The browser cases execute
a real native Stop with failed resource release at 1024×768 and 1440×900.

The initial six-case red and reviewed eight-case red are retained separately.
Ownership review changed the substitution expectation to unknown and added real
replacement/missing cases. Both browser reds fail on the missing resource panel
after the actual API facts pass. Exact source maps are retained per execution;
380 selected inputs are individually unchanged within each phase, while source,
compiled UI and ADR changes between phases remain explicit.

Current625 browser cases across60 files are collected, not fully executed.
The previous1,211/86/2/package115 proof remains tied to `0bc939d` and does not
verify this successor. The full lifecycle fault matrix, supported live-tune,
held native Windows, live/provider/physical/human/AT/SADS and independent acceptance
remain open. Counts stay49 completed/41 in progress/10 blocked; zero milestones.
