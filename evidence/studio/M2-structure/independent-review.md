# Independent review — model structure canvas and keyboard tree (2026-10-25)

A separate read-only reviewer inspected the first T043 candidate against FR-023, FR-027, NFR-006,
AC-013/AC-031, AGENTS.md separation rules and the pinned XDL System schema. The first full run of that
candidate also failed two existing browser checks (an extra breadcrumb "plant" button and a duplicate
"Unplaced" text made strict selectors ambiguous); both are retained as recorded failures and repaired.

| # | Finding | Disposition |
|---|---|---|
| 1 | Elements without a node were shown as an "undeclared node" named "Unplaced", with a declaration link to nothing; a real node named `Unplaced` would merge with them. | Placement is explicit (`declared`/`undeclared`/`unplaced`); unplaced elements form a separate group with no declaration link; a literal `Unplaced` node stays declared (tested). |
| 2 | `node.memberIds` was ignored. | Membership is the union of `nodeId` and `memberIds`; members listed only by `memberIds` are marked "(listed)" with their actual placement. |
| 3 | Frames wrapped whatever layout was current and could misdescribe placement. | Enabling grouping arranges by node (not saved); a status message appears whenever a frame covers a non-member. |
| 4 | Undeclared status was visible only by colour. | A visible "(undeclared)"/"(unplaced)" marker; frames carry text. Selection also has a non-colour marker. |
| 5 | Search and expansion state disagreed; group-name matches hid members; no empty state. | One expansion rule for rendering and keys; matching groups show all members; a "no matches" row. |
| 6 | Frame and tree computations were quadratic. | Single-pass membership maps; tree items carry their element. |
| 7 | Grouped layout did not scale (one column per node). | Near-square member blocks with wrapped group rows. |
| 8 | Nodes used deployment imagery. | Neutral folder icon; text states node placement is not a deployment target. |

Speculative items addressed: breadcrumb no longer repeats a node-kind element; current location is
text (`aria-current`), a link back only below a definition; focus outline on the label; tree ignores
modified keys; Component parameters are shown; tests assert exact saved keys and no frame overlap.

Retained limitations: canvas edges connect elements, with endpoint names shown as labels and in the
inspector, not as per-port handles; there is no type-ahead; moving an element between nodes requires a
source edit because no admitted semantic edit changes `nodeId`; XDL v1alpha1 has no nested Systems, so
subsystem navigation is node and Component-definition drill-down.
