# Neutral logical asset review

Reviewer: root, separate from backend asset authoring. Read-only review of initial asset successor `xdl/edits.py` SHA256 `4a069771a705b4d693691accb9f95f42a278b507c219f64c6989933d64a6d508` before the repair below.

- ASSET-R01: adding a Device without nodeId is possible, but a placed Device cannot become unplaced through the update operation. Sending null fails the authoritative schema. This leaves placement unnecessarily sticky rather than independent. Repair requested: an explicit bounded optional-property removal operation, with immutable identity/required fields protected; test placed → unplaced and realization class unchanged.
- ASSET-R02: Sensor/Actuator deviceId and endpoint references can point to different endpoint owners. Source inspection confirms this is allowed by the pinned public schema and semantics (existence checks are independent). No stronger ownership rule is invented. The authoring interface must retain these as independent choices.

No native Windows test or physical operation was requested by this review. Complete T049/T051/T052 acceptance remains open beyond the reviewed slice. The previously completed T044 selected-resource source-navigation claim is under repair, with a browser check required before it remains complete.

ASSET-R01 successor reviewed: `xdl/edits.py` SHA256 `b6547b5374b3a900981b632099901a4544be32370c4207308cc751d0383ce4cf` implements explicit allowlisted `unsetProperties`, rejecting required/identity fields and conflicting update/removal. The author retained 41 passing affected tests, including placed → unplaced with realization/identity preserved. Backend finding closed for this component; browser integration remains pending.
