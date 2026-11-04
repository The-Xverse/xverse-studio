import type { Data } from "../../api/types";
import { Json, KeyValues } from "../../app/ui";

const statuses = new Set(["valid", "verified_prefix", "invalid", "unavailable"]);
const integrity = (value: unknown) => typeof value === "string" && statuses.has(value) ? value : "Unconfirmed";
const reasons: Record<string, string> = {
  SOURCE_PROVIDER_READER_UNSUPPORTED: "The original provider reader is unavailable here. Import does not install it.",
  ORIGINAL_JOURNAL_INVALID: "The recorded journal structure or hashes failed verification. Preserve the source archive.",
  DECLARED_AND_OBSERVED_INTEGRITY_DIFFER: "The original report and current inspection differ; both are shown separately.",
  DEPENDENCY_SUMMARY_UNAVAILABLE: "This older report has no supported dependency summary.",
  COMPILED_PROFILE_DEPENDENCY_SUMMARY_UNAVAILABLE: "This older dependency summary omits the compiled profile. Preserve and inspect the original snapshot for those declarations.",
  IMPORTED_FILES_CHANGED_OR_UNAVAILABLE: "Stored imported files changed or cannot be safely read. The original report is retained.",
  EFFECTIVE_INPUT_IDENTITY_UNPROVEN: "Recorded effective inputs do not match the original frozen identities.",
};

export function EvidenceInspection({ bundle }: { bundle: Data }) {
  const inspection = bundle.inspection || {}, report = bundle.report || {};
  const summary = inspection.dependencies;
  const supported = ["1.0", "1.1"].includes(summary?.dependenciesVersion) && summary?.resolution === "not_attempted" &&
    Array.isArray(summary.items) && summary.items.length <= 256 && summary.items.every((row: Data) => row &&
      ["provider", "compiler", "profile", "artifact"].includes(row.kind) && row.contentIncluded === false &&
      ["not_included", "unavailable"].includes(row.availability));
  const evaluations = Array.isArray(bundle.evaluations) ? bundle.evaluations : [];
  const annotations = Array.isArray(bundle.annotations) ? bundle.annotations : [];
  const diagnostics = Array.isArray(inspection.diagnostics) ? inspection.diagnostics.slice(0, 32) : [];
  return <>
    <p>This is recorded evidence inspection. Import creates no run and grants no execution authority.</p>
    <section aria-label="Current imported evidence inspection">
      <h3>Current inspection</h3>
      <KeyValues values={{
        Bundle: bundle.bundleId,
        "Archive digest": bundle.archiveDigest,
        "Current integrity": integrity(inspection.integrity),
        "Current availability": inspection.availability,
        "Source run": inspection.sourceRunId,
        "Source snapshot": inspection.sourceSnapshotId,
        "Source provider": inspection.sourceProviderId,
        "Execution allowed": inspection.executionAllowed === false ? "No" : "Unconfirmed; import never grants authority",
      }} />
    </section>
    <section aria-label="Original imported evidence report">
      <h3>Original report</h3>
      <p>These are preserved source claims. Current inspection does not rewrite them.</p>
      <KeyValues values={{ "Reported integrity": integrity(report.integrity), "Reported evidence status": report.evidenceStatus,
        "Reported scope": report.evidenceScope, "Original plan digest": report.planDigest }} />
    </section>
    {diagnostics.length > 0 && <ul aria-label="Import diagnostics">{diagnostics.map((code: string, i: number) =>
      <li key={i}><code>{String(code)}</code> — {reasons[code] || "This source needs further inspection; no execution is admitted."}</li>)}</ul>}
    <section aria-label="Referenced dependencies">
      <h3>Referenced dependencies</h3>
      <p>Frozen identities are metadata. Runtime, compiler, profile and artifact payloads are not included, fetched or installed. Their availability on this host has not been checked.</p>
      {supported ? <div className="table-scroll"><table>
        <caption>Dependency references</caption>
        <thead><tr><th>Kind</th><th>Frozen identity</th><th>Payload in bundle</th></tr></thead>
        <tbody>{summary.items.map((row: Data, i: number) => <tr key={i}>
          <th scope="row">{row.kind}</th>
          <td><details><summary>Inspect {row.kind} identity</summary><Json value={row.identity} expanded /></details></td>
          <td>{row.availability === "not_included" ? "Not included" : "Unavailable"}</td>
        </tr>)}</tbody>
      </table></div> : <p role="status">Dependency summary is unavailable or unsupported. Inspect the preserved source metadata.</p>}
    </section>
    <section aria-label="Preserved derived records">
      <h3>Preserved derived records</h3>
      <p>{evaluations.length} recorded evaluations and {annotations.length} annotations. Import does not reevaluate assertions or change a reported verdict.</p>
      <details><summary>Inspect recorded evaluations and annotations</summary><Json value={{ evaluations, annotations }} expanded /></details>
    </section>
    <details><summary>Complete imported metadata</summary><Json value={bundle} expanded /></details>
  </>;
}
