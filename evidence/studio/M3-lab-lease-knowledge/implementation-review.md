# Affected implementation review

Finding1: confirmed terminal records were overwritten as unknown on restore.
Finding2: all typed provider errors were treated as definite refusal, discarding
intent after an uncertain acquired lease. Finding3: known uncertain authority still
contacted provider inventory. Original5 failures and the passing busy control are
retained. The repair keeps terminal facts, preserves unknown intent with no fence
invention/reacquisition, and denies uncertain/terminal authority before provider IO.
RESOURCE_BUSY remains the existing definite typed-conflict contract. Other failures
retain uncertainty. Owned-path capability, principal, scope, fence and expiry checks
remain. Existing main test AST nodes are unchanged; six regression cases are added.

The final full944 backend suite and83 affected browser checks pass against identical
300 selected inputs. No default admitted provider, physical authority or positive
HTTP route is introduced. The tested physical provider is explicitly a fixture
without equipment IO. Existing unadmitted HTTP refusal remains. Root review cannot
establish live-provider, actual AT/human, Windows or full milestone acceptance.
