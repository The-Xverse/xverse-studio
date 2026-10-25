import { useState } from "react";
import type { Data } from "../../api/types";
import { Badge, Json, KeyValues, Modal } from "../../app/ui";
export function FrozenInputs({
  snapshot,
  onClose,
}: {
  snapshot: Data;
  onClose: () => void;
}) {
  const [scope, setScope] = useState<"documents" | "projectDocuments">(
      "documents",
    ),
    [document, setDocument] = useState(
      Object.keys(snapshot.documents || {})[0] || "",
    );
  const documents: Record<string, string> =
    snapshot[scope] || snapshot.documents || {};
  const selected =
    document in documents ? document : Object.keys(documents)[0] || "";
  return (
    <Modal
      title="Frozen run inputs · read-only"
      wide
      restoreFocusSelector="[data-frozen-inputs-trigger]"
      onClose={onClose}
    >
      <p>
        These verified source inputs belong to this immutable run snapshot.
        Current project edits create separate draft revisions.
      </p>
      <div className="frozen-snapshot-summary">
        <Badge tone="success">Backend integrity verified</Badge>
        <KeyValues
          values={{
            Snapshot: snapshot.snapshotId,
            "Project revision": snapshot.revision,
            "Snapshot identity": snapshot.snapshotDigest,
            "Plan identity": snapshot.planDigest,
            "Semantic identity": snapshot.semanticDigest,
            "Selected Deployment":
              snapshot.selection?.deploymentRef || "Single declared deployment",
            "Selected Scenario":
              snapshot.selection?.scenarioRef || "Single declared scenario",
          }}
        />
      </div>
      <div className="source-toolbar">
        <label>
          Input set
          <select
            aria-label="Frozen input set"
            value={scope}
            onChange={(event) =>
              setScope(event.target.value as "documents" | "projectDocuments")
            }
          >
            <option value="documents">Compiled contributing inputs</option>
            <option value="projectDocuments">Complete authored revision</option>
          </select>
        </label>
        <label>
          Frozen document
          <select
            aria-label="Frozen document"
            value={selected}
            onChange={(event) => setDocument(event.target.value)}
          >
            {Object.keys(documents).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="source-pane-label" htmlFor="frozen-source">
        Frozen source text (read-only)
      </label>
      <textarea
        id="frozen-source"
        aria-label="Frozen source text (read-only)"
        readOnly
        spellCheck={false}
        className="source-textarea"
        value={documents[selected] || ""}
      />
      <Json
        value={{
          configuration: snapshot.configuration,
          compiler: snapshot.compiler,
          profileLocks: snapshot.profileLocks,
          providerIdentity: snapshot.providerIdentity,
          projectRevisionInputsDigest: snapshot.projectRevisionInputsDigest,
        }}
      />
    </Modal>
  );
}
