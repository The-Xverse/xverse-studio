import { test, expect } from "@playwright/test";
import { compareDraft } from "../../apps/studio-web/src/features/model/run-overlay";
import { projectDisplay } from "../../apps/studio-web/src/features/model/projection";
import type { Project } from "../../apps/studio-web/src/api/types";

const system = (nodes: object[], instances: object[]) =>
  JSON.stringify({
    apiVersion: "xverse.io/xdl/v1alpha1",
    kind: "System",
    metadata: { namespace: "org.example", name: "s" },
    spec: { nodes, componentInstances: instances },
  });
const scenario = (name: string, value: number) =>
  JSON.stringify({
    apiVersion: "xverse.io/xdl/v1alpha1",
    kind: "Scenario",
    metadata: { namespace: "org.example", name },
    spec: {},
    extensions: {
      "io.xverse.experiment": {
        parameters: [{ id: "duration", valueType: "number", value }],
      },
    },
  });
const instance = (id: string, nodeId: string) => ({
  id,
  nodeId,
  componentRef: { kind: "Component", namespace: "org.example", name: "c" },
});
function project(documents: Record<string, string>, profiles: object[] = []) {
  return {
    projectId: "p",
    name: "p",
    revision: 3,
    manifest: { profiles },
    documents: Object.fromEntries(
      Object.entries(documents).map(([path, content]) => [
        "id-" + path,
        { path, content, format: "json" },
      ]),
    ),
  } as unknown as Project;
}
function compare(draft: Project, snapshot: Record<string, unknown>) {
  const frozen = projectDisplay(
    project(snapshot.documents as Record<string, string>),
  );
  return compareDraft(draft, projectDisplay(draft), frozen, "run-1", {
    snapshotId: "snap-1",
    revision: 2,
    ...snapshot,
  });
}

test("run overlay compares with the executed inputs, not the authored revision", () => {
  const authored = {
    "xdl/system.json": system(
      [{ id: "n", roles: ["r"] }],
      [instance("a", "n")],
    ),
    "xdl/run.json": scenario("run", 5),
  };
  // A campaign child executed a rewritten scenario while projectDocuments stayed authored.
  const result = compare(project(authored), {
    projectDocuments: authored,
    documents: { ...authored, "xdl/run.json": scenario("run", 9) },
    selection: { scenarioRef: "xdl://org.example/scenario/run" },
  });
  expect(result.runInputChanges).toBe(2);
  expect(result.documents).toEqual([
    { path: "xdl/run.json", change: "changed" },
  ]);
  expect(result.parameters).toEqual([
    {
      key: "xdl://org.example/scenario/run#duration",
      id: "duration",
      draft: 5,
      run: 9,
      change: "changed",
    },
  ]);
});

test("run overlay ignores unused documents and other scenarios but counts profile locks", () => {
  const executed = {
    "xdl/system.json": system(
      [{ id: "n", roles: ["r"] }],
      [instance("a", "n")],
    ),
    "xdl/run.json": scenario("run", 5),
  };
  const draft = project(
    { ...executed, "xdl/other.json": scenario("other", 7) },
    [{ namespace: "io.example", version: "2.0.0" }],
  );
  const result = compare(draft, {
    documents: executed,
    profileLocks: [{ namespace: "io.example", version: "1.0.0" }],
    selection: { scenarioRef: "xdl://org.example/scenario/run" },
  });
  expect(result.otherDocuments).toEqual(["xdl/other.json"]);
  expect(result.documents).toEqual([]);
  expect(result.parameters).toEqual([]);
  expect(result.profileLocksChanged).toBe(true);
  expect(result.runInputChanges).toBe(1);
});

test("placing an instance on an empty node is an added element, not a removed node", () => {
  const before = {
    "xdl/system.json": system(
      [
        { id: "n", roles: ["r"] },
        { id: "empty", roles: ["spare"] },
      ],
      [instance("a", "n")],
    ),
  };
  const after = project({
    "xdl/system.json": system(
      [
        { id: "n", roles: ["r"] },
        { id: "empty", roles: ["spare"] },
      ],
      [instance("a", "n"), instance("b", "empty")],
    ),
  });
  const result = compare(after, { documents: before });
  expect(result.nodes).toEqual([]);
  expect(result.elements).toEqual([
    { ref: "xdl://org.example/system/s#b", name: "b", change: "added" },
  ]);
});
