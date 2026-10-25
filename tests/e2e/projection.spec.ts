import { test, expect } from "@playwright/test";
import { projectDisplay } from "../../apps/studio-web/src/features/model/projection";
import type { Project } from "../../apps/studio-web/src/api/types";
test("malformed imported source stays inspectable without becoming a graph or changing bytes", () => {
  const content =
    "apiVersion: xverse.io/xdl/v1alpha1\nkind: System\nmetadata:\n  name: {unsupported: value}\nspec:\n  componentInstances: {unexpected: object}\n  nodes: invalid\n";
  const project = {
    projectId: "owned-fixture",
    name: "Untrusted source",
    revision: 1,
    documents: { source: { content, format: "yaml", path: "xdl/source.yaml" } },
  } as Project;
  const display = projectDisplay(project);
  expect(display.elements).toEqual([]);
  expect(display.parseErrors).toContain("source");
  expect(display.resources[0].metadata.name).toBe("source");
  expect((project.documents.source as { content: string }).content).toBe(
    content,
  );
});
test("unknown extension payload is retained while the presentation uses stable instance references", () => {
  const content = JSON.stringify({
    apiVersion: "xverse.io/xdl/v1alpha1",
    kind: "System",
    metadata: { name: "fixture" },
    spec: {
      nodes: [{ id: "host", roles: ["reference"] }],
      componentInstances: [
        {
          id: "element",
          nodeId: "host",
          componentRef: { kind: "Component", name: "component" },
        },
      ],
    },
    extensions: {
      "unresolved.example": { script: "inert text", opaque: [1, 2, 3] },
    },
  });
  const project = {
    projectId: "fixture",
    name: "Fixture",
    revision: 1,
    documents: { source: { content, format: "json", path: "xdl/source.json" } },
  } as Project;
  const display = projectDisplay(project);
  expect(display.elements[0].id).toBe("element");
  expect(display.resources[0].extensions["unresolved.example"].opaque).toEqual([
    1, 2, 3,
  ]);
  expect((project.documents.source as { content: string }).content).toBe(
    content,
  );
});

test("declared logical roles remain separate from Component capabilities and source bytes", () => {
  const system = JSON.stringify({
    apiVersion: "xverse.io/xdl/v1alpha1",
    kind: "System",
    metadata: { namespace: "org.example", name: "system" },
    spec: {
      nodes: [{ id: "logical-node", roles: ["plant"] }],
      componentInstances: [
        {
          id: "logical-instance",
          nodeId: "logical-node",
          componentRef: {
            kind: "Component",
            namespace: "org.example",
            name: "definition",
          },
        },
      ],
    },
  });
  const definition = JSON.stringify({
    apiVersion: "xverse.io/xdl/v1alpha1",
    kind: "Component",
    metadata: { namespace: "org.example", name: "definition" },
    spec: { capabilities: ["response-model"] },
  });
  const project = {
    projectId: "display-only",
    name: "Role display",
    revision: 1,
    documents: {
      system: { content: system, format: "json", path: "system.xdl.json" },
      definition: {
        content: definition,
        format: "json",
        path: "component.xdl.json",
      },
    },
  } as Project;
  const display = projectDisplay(project);
  expect(display.elements[0].role).toBe("plant");
  expect(display.elements[0].definition?.spec.capabilities).toEqual([
    "response-model",
  ]);
  expect((project.documents.system as { content: string }).content).toBe(
    system,
  );
});
