# Neutral asset authoring findings before repair

Inspected 2026-10-25, Linux, public XDL baseline 7fab6a290c3731533c2b88517158055c768b9d4e.

1. Add element and semantic add_element support Component instances only. The public System schema already defines logical devices, sensors, actuators and model references, so these otherwise valid logical assets require manual source authoring. This leaves T049/T051/T052 and FR-032 incomplete.
2. Browser projectDisplay projects componentInstances and nodes but omits devices/sensors/actuators/models, whereas backend XDLAdapter.project exposes all six collections. Valid authored assets are invisible in canvas/table selection.
3. This slice can use existing XDL schema and reference validation without a provider, physical asset, download, build or execution. Added topology must continue to fail the owned reference provider admission; authoring does not establish executable support.

Planned repair: closed atomic add/update logical asset edits, public full-source validation, stable resource-qualified target checks, independent capability/placement properties, bounded optional endpoint bundles, and browser projection/forms. Existing component-instance operation stays available. Round-trip YAML preserves supported comments/unknown data; no claim of byte-identical formatting for changed documents. Linux checks only; Windows installation/testing is held at user request.
