# Independent review: round-trip CLI tests

A first review run stalled; a time-boxed re-review produced these confirmed findings and repairs:

| Finding | Repair |
| --- | --- |
| Equal-identity checks could pass with both tools rejecting a case (`None == None`), because the baseline validity was unchecked | The baseline must be valid with digests; "equal" cases must be valid |
| The broken-draft step only required one shared diagnostic code | Requires identical validity and codes from both tools |
| No CLI-backed conflicting-write case (SC-002) | After the `412`, both tools report the pre-conflict identity for the stored bytes |
| The CLI received flattened basenames, not Studio's relative paths | Writes the same relative paths; names were shown not to affect digests |
| The CLI exit code and stderr were ignored | No traceback allowed; the exit code must match the reported validity |
| A global `cases` module on `sys.path` could shadow or be shadowed | Loaded under a unique module name via `importlib` |
