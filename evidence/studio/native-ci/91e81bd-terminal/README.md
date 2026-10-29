# Completed CI for the earlier live-target candidate

Both Ubuntu24 push and PR jobs completed successfully. Their decoded logs report
1,250 backend tests, all629 browser cases and the116-file package smoke passing.
[Push receipt](push-receipt.json), [PR receipt](pr-receipt.json),
[combined source-bound record](../ubuntu-24.04-91e81bd-runs.json).

The push checkout is91e81bd. The PR checkout is synthetic mergec7a66dcf; GitHub's
Git object API confirms both have tree9775430403370c034c7958364658d2cd6a239d32.
Their environment records share the same source digest. The independently
reported package candidates and archive hashes remain separate.

These jobs precede the native late-command tests introduced inddc1ad6 and the
cleanup/pre-launch recovery successor. They do not resolve the later local
1264pass/1fail result or establish a passing full suite for that successor.
Native Windows, live/physical and milestone gates remain open.

Decoded job logs and summaries are retained. Artifact IDs, sizes and server
digests are recorded for provenance; archives were not downloaded or independently
payload-verified during this reconciliation. Reported package smoke results retain
their stated prepared-cache offline/native Linux scope.
