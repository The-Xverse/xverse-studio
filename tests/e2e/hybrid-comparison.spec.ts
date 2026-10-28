import { test, expect, type Page, type Locator } from "@playwright/test";
import { connectStudio } from "./connect-studio";
import { parse, stringify } from "yaml";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 200; i++) {
    if (await target.evaluate((n) => n === document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error(
    "Comparison control is not reachable through native Tab order.",
  );
}
async function choose(page: Page, target: Locator, value: string) {
  const options = await target
    .locator("option")
    .evaluateAll((nodes) =>
      nodes
        .filter((n) => !(n as HTMLOptionElement).disabled)
        .map((n) => (n as HTMLOptionElement).value),
    );
  const index = options.indexOf(value);
  expect(index).toBeGreaterThanOrEqual(0);
  await tabTo(page, target);
  await page.keyboard.press("Home");
  for (let i = 0; i < index; i++) await page.keyboard.press("ArrowDown");
  await expect(target).toHaveValue(value);
}
async function save(
  page: Page,
  project: any,
  documentId: string,
  content: string,
) {
  return page.evaluate(
    async ({ projectId, revision, documentId, content }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const response = await fetch(
        `/api/v1/projects/${projectId}/documents/${documentId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
            "If-Match": String(revision),
          },
          body: JSON.stringify({ content }),
        },
      );
      if (response.status !== 200)
        throw new Error(
          `Owned comparison source preparation failed: ${response.status} ${(await response.json()).code}`,
        );
      return response.json();
    },
    {
      projectId: project.projectId,
      revision: project.revision,
      documentId,
      content,
    },
  );
}
async function prepare(
  page: Page,
  name: string,
  configuration: "plain" | "mappings" | "physical" | "pages" = "plain",
) {
  const value = await page.evaluate(async (name) => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const headers = {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    };
    const created = await fetch("/api/v1/projects", {
      method: "POST",
      headers,
      body: JSON.stringify({ name }),
    });
    if (created.status !== 201)
      throw new Error("Owned comparison Project creation failed.");
    const project = await created.json(),
      url = `/api/v1/projects/${project.projectId}/deployment-variants`;
    const left = (await fetch(url).then((r) => r.json())).items[0];
    const cloned = await fetch(url, {
      method: "POST",
      headers: { ...headers, "If-Match": String(project.revision) },
      body: JSON.stringify({
        name: "Comparison candidate",
        baseRevision: project.revision,
      }),
    });
    if (cloned.status !== 201)
      throw new Error(
        `Owned comparison variant creation failed: ${cloned.status} ${(await cloned.json()).code}`,
      );
    const result = await cloned.json();
    localStorage.setItem("studio.projectId", project.projectId);
    return { project: result.project, left, right: result.variant };
  }, name);
  if (configuration !== "plain") {
    const deployment = parse(
      value.project.documents[value.right.documentId].content,
    );
    if (configuration === "mappings") {
      const [systemId, document]: any = Object.entries(
        value.project.documents,
      ).find(([, d]: any) => d.path.endsWith("/system.xdl.yaml"));
      const system = parse(document.content);
      system.spec.timeDomains.push({
        id: "wall-time",
        clockClass: "wall",
        epoch: "unix",
        rate: "1",
        monotonic: false,
      });
      value.project = await save(
        page,
        value.project,
        systemId,
        stringify(system),
      );
      deployment.spec.timeMappings = [
        {
          id: "wall-to-sim",
          sourceTimeDomainRef: {
            ...deployment.spec.systemRef,
            element: "wall-time",
          },
          targetTimeDomainRef: {
            ...deployment.spec.systemRef,
            element: "simulation-time",
          },
          mapping: "offset-at-start",
          tolerance: { value: 0.001, unit: "s" },
        },
      ];
    } else if (configuration === "physical") {
      deployment.spec.bindings.find(
        (b: any) => b.id === "plant-binding",
      ).realizationClass = "physical";
      deployment.spec.targets[0].externalAssetRef =
        "urn:fixture:unadmitted-browser-bench";
      deployment.spec.targets[0].capabilities.push("pause");
    } else {
      const first = deployment.spec.targets[0];
      deployment.spec.targets = [
        first,
        ...Array.from({ length: 50 }, (_, i) => ({
          ...first,
          id: `target-${String(i + 1).padStart(3, "0")}`,
        })),
      ];
    }
    value.project = await save(
      page,
      value.project,
      value.right.documentId,
      stringify(deployment),
    );
    if (configuration === "mappings") {
      const [scenarioId, document]: any = Object.entries(
        value.project.documents,
      ).find(([, d]: any) =>
        d.path.endsWith("/scenario-comparison-candidate.xdl.yaml"),
      );
      const scenario = parse(document.content);
      scenario.spec.timeMappings = [
        {
          sourceTimeDomainId: "wall-time",
          targetTimeDomainId: "simulation-time",
          mapping: "offset-at-start",
          tolerance: { value: 0.02, unit: "s" },
        },
      ];
      value.project = await save(
        page,
        value.project,
        scenarioId,
        stringify(scenario),
      );
    }
  }
  await page.reload();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  const deployment = page.getByRole("tab", { name: /Deployment/ });
  await tabTo(page, deployment);
  await page.keyboard.press("Enter");
  const selected = page.getByLabel("Deployment variant", { exact: true });
  await expect
    .poll(() =>
      selected
        .locator("option")
        .evaluateAll((nodes) =>
          nodes.map((n) => (n as HTMLOptionElement).value),
        ),
    )
    .toContain(value.left.ref);
  await choose(page, selected, value.left.ref);
  return value;
}
for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  test.describe(`hybrid comparison: coherent declarations at ${viewport.width}`, () => {
    test.use({ viewport });
    test("native comparison separates declared clocks and controls from physical evidence", async ({
      page,
    }, info) => {
      await connectStudio(page, info);
      const value = await prepare(page, `Comparison ${viewport.width}`);
      const before = await page.request
        .get(`/api/v1/projects/${value.project.projectId}`)
        .then((r) => r.json());
      await choose(
        page,
        page.getByLabel("Comparison variant"),
        value.right.ref,
      );
      const existing = page.getByRole("region", {
        name: "Compare realization and placement",
        exact: true,
      });
      await expect(existing).toContainText(
        "logical element identities are shared",
      );
      const evidence = page.getByRole("region", {
        name: "Time, control and physical evidence",
        exact: true,
      });
      await expect(evidence).toContainText(
        `Captured project revision: ${value.project.revision}`,
      );
      await expect(evidence).toContainText("Unmeasured");
      await expect(evidence).toContainText("Physical state");
      await expect(evidence).toContainText("Unknown");
      await expect(evidence).toContainText("Unverified");
      await expect(evidence).toContainText("simulation-time");
      await expect(evidence).toContainText("start, stop, cancel");
      expect(
        await page.request
          .get(`/api/v1/projects/${value.project.projectId}`)
          .then((r) => r.json()),
      ).toEqual(before);
      expect(
        (
          await page.request.get("/api/v1/runs").then((r) => r.json())
        ).items.filter((r: any) => r.projectId === value.project.projectId),
      ).toEqual([]);
    });

    for (const configuration of ["mappings", "physical", "pages"] as const) {
      test(`actual ${configuration} declarations preserve source and separate capability evidence`, async ({
        page,
      }, info) => {
        await connectStudio(page, info);
        const value = await prepare(
          page,
          `Comparison ${configuration} ${viewport.width}`,
          configuration,
        );
        const before = await page.request
          .get(`/api/v1/projects/${value.project.projectId}`)
          .then((r) => r.json());
        await choose(
          page,
          page.getByLabel("Comparison variant"),
          value.right.ref,
        );
        const evidence = page.getByRole("region", {
          name: "Time, control and physical evidence",
          exact: true,
        });
        await expect(evidence).toContainText(
          `Captured project revision: ${value.project.revision}`,
        );
        await expect(evidence).toContainText("Unmeasured");
        if (configuration === "mappings") {
          const mappings = evidence.getByRole("region", {
            name: "comparison-candidate: declared mappings",
            exact: true,
          });
          await expect(mappings).toContainText("wall-to-sim");
          await expect(mappings).toContainText("#wall-time");
          await expect(mappings).toContainText("#simulation-time");
          await expect(mappings).toContainText("0.001 s; accuracy unmeasured");
          await expect(mappings).toContainText("/spec/timeMappings/0");
          await expect(mappings).toContainText("0.02 s; accuracy unmeasured");
          await expect(mappings.getByRole("row")).toHaveCount(3);
        } else if (configuration === "physical") {
          const binding = page
            .getByRole("region", {
              name: "Compare realization and placement",
              exact: true,
            })
            .getByRole("row", { name: /plant/ });
          await expect(binding).toContainText("physical");
          await expect(binding).toContainText("unsupported");
          await expect(evidence).toContainText("CAPABILITY_UNSUPPORTED");
          const targets = evidence.getByRole("region", {
            name: "comparison-candidate: declared targets",
            exact: true,
          });
          await expect(targets).toContainText("pause");
          await expect(evidence.locator("dl")).toContainText(
            "start, stop, cancel",
          );
          expect(await evidence.textContent()).not.toContain(
            "urn:fixture:unadmitted-browser-bench",
          );
        } else {
          const targets = evidence.getByRole("region", {
            name: "comparison-candidate: declared targets",
            exact: true,
          });
          await expect(targets.getByRole("row")).toHaveCount(51);
          await expect(targets).toContainText("Showing 1–50 of 51");
          const next = targets.getByRole("button", {
            name: "Next declared targets for comparison-candidate",
            exact: true,
          });
          await tabTo(page, next);
          await page.keyboard.press("Enter");
          await expect(targets.getByRole("heading")).toBeFocused();
          await expect(targets.getByRole("row")).toHaveCount(2);
          await expect(targets).toContainText("target-050");
        }
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth + 1,
          ),
        ).toBe(true);
        expect(
          await page.request
            .get(`/api/v1/projects/${value.project.projectId}`)
            .then((r) => r.json()),
        ).toEqual(before);
        expect(
          (
            await page.request.get("/api/v1/runs").then((r) => r.json())
          ).items.filter((r: any) => r.projectId === value.project.projectId),
        ).toEqual([]);
      });
    }

    test("actual stale revision refuses before comparison instead of adopting newer source", async ({
      page,
    }, info) => {
      await connectStudio(page, info);
      const value = await prepare(page, `Stale comparison ${viewport.width}`);
      let requests = 0,
        observed: any = null;
      await page.route("**/comparison?**", async (route) => {
        requests++;
        if (requests === 1)
          await save(
            page,
            value.project,
            value.right.documentId,
            value.project.documents[value.right.documentId].content +
              "\n# owned concurrent writer\n",
          );
        const response = await route.fetch();
        observed = {
          status: response.status(),
          code: (await response.json()).code,
          requestedRevision: value.project.revision,
        };
        await route.fulfill({ response });
      });
      try {
        await choose(
          page,
          page.getByLabel("Comparison variant"),
          value.right.ref,
        );
        await expect(
          page
            .getByRole("alert")
            .filter({ hasText: "Deployment comparison unavailable" }),
        ).toContainText("REVISION_CONFLICT");
        expect(observed.status).toBe(412);
        expect(observed.code).toBe("REVISION_CONFLICT");
        await expect(
          page.getByRole("region", {
            name: "Time, control and physical evidence",
            exact: true,
          }),
        ).toHaveCount(0);
        expect(requests).toBe(1);
        await info.attach("actual-concurrent-source-refusal", {
          body: JSON.stringify(observed),
          contentType: "application/json",
        });
      } finally {
        await page.unrouteAll({ behavior: "wait" });
      }
    });

    for (const malformed of [
      "project",
      "revision",
      "provider",
      "document",
      "source",
      "physical",
      "clock",
      "binding",
      "size",
      "tree",
    ] as const) {
      test(`labelled malformed ${malformed} response is unavailable`, async ({
        page,
      }, info) => {
        await connectStudio(page, info);
        const value = await prepare(
          page,
          `Invalid comparison ${malformed} ${viewport.width}`,
        );
        await page.route("**/comparison?**", async (route) => {
          const response = await route.fetch();
          expect(response.status()).toBe(200);
          const data = await response.json();
          if (malformed === "project") data.projectId = "foreign-project";
          if (malformed === "revision") data.revision++;
          if (malformed === "provider") data.providerId = "foreign-provider";
          if (malformed === "document")
            data.right.resolution.documentId = "foreign-document";
          if (malformed === "source")
            data.sharedSystem.sourceDigest = "not-a-digest";
          if (malformed === "physical") data.physicalState = "stopped_observed";
          if (malformed === "clock")
            data.synchronization.preciseLatencyAvailable = true;
          if (malformed === "binding")
            data.right.resolution.bindings[0].targetId = "misbound-target";
          if (malformed === "size")
            data.right.declaredTargets = Array(1001).fill(
              data.right.declaredTargets[0],
            );
          if (malformed === "tree") {
            let nested: any = 1;
            for (let i = 0; i < 40; i++) nested = { nested };
            data.right.resolution.parameters[0].chain[0].value = nested;
          }
          await route.fulfill({ response, body: JSON.stringify(data) });
        });
        try {
          await choose(
            page,
            page.getByLabel("Comparison variant"),
            value.right.ref,
          );
          await expect(
            page
              .getByRole("alert")
              .filter({ hasText: "Deployment comparison unavailable" }),
          ).toContainText("Comparison metadata");
          await expect(
            page.getByRole("region", {
              name: "Compare realization and placement",
              exact: true,
            }),
          ).toHaveCount(0);
          await info.attach("controlled-comparison-response", {
            body: JSON.stringify({
              scope:
                "Labelled transport corruption after actual HTTP200; not a provider observation",
              malformed,
              viewport,
            }),
            contentType: "application/json",
          });
        } finally {
          await page.unrouteAll({ behavior: "wait" });
        }
      });
    }

    for (const intent of ["Home", "selection", "focus", "dialog"] as const) {
      test(`held real response respects newer ${intent} intent`, async ({
        page,
      }, info) => {
        await connectStudio(page, info);
        const value = await prepare(
          page,
          `Held comparison ${intent} ${viewport.width}`,
        );
        let release!: () => void, announce!: () => void;
        const gate = new Promise<void>((resolve) => {
            release = resolve;
          }),
          seen = new Promise<void>((resolve) => {
            announce = resolve;
          });
        let captured = false;
        await page.route("**/comparison?**", async (route) => {
          if (captured) {
            await route.fallback();
            return;
          }
          captured = true;
          const response = await route.fetch();
          expect(response.status()).toBe(200);
          const body = await response.body();
          announce();
          await gate;
          if (intent === "Home" || intent === "selection") {
            await expect
              .poll(() => route.request().failure()?.errorText)
              .toBe("net::ERR_ABORTED");
            await route.fallback();
            await info.attach("actual-browser-comparison-cancellation", {
              body: JSON.stringify({
                scope: "Browser transport only; no physical cancellation claim",
                intent,
                failure: "net::ERR_ABORTED",
              }),
              contentType: "application/json",
            });
          } else {
            await route.fulfill({ response, body });
          }
        });
        try {
          await choose(
            page,
            page.getByLabel("Comparison variant"),
            value.right.ref,
          );
          await seen;
          if (intent === "Home") {
            const home = page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            });
            await tabTo(page, home);
            await page.keyboard.press("Enter");
          } else if (intent === "selection")
            await choose(
              page,
              page.getByLabel("Deployment variant", { exact: true }),
              value.right.ref,
            );
          else if (intent === "focus")
            await tabTo(
              page,
              page.getByLabel("Associated Scenario", { exact: true }),
            );
          else
            await page.evaluate(() => {
              const dialog = document.createElement("dialog");
              dialog.setAttribute("aria-label", "Controlled comparison dialog");
              dialog.innerHTML =
                "<label>Controlled dialog field<input autofocus></label>";
              document.body.append(dialog);
              dialog.showModal();
            });
          release();
          await page.unrouteAll({ behavior: "wait" });
          if (intent === "Home") {
            await expect(
              page.getByRole("heading", {
                name: "Start with an example",
                exact: true,
              }),
            ).toBeVisible();
            await expect(
              page.getByRole("region", {
                name: "Time, control and physical evidence",
                exact: true,
              }),
            ).toHaveCount(0);
          } else if (intent === "selection") {
            await expect(
              page.getByLabel("Deployment variant", { exact: true }),
            ).toHaveValue(value.right.ref);
            await expect(
              page.getByRole("region", {
                name: "Time, control and physical evidence",
                exact: true,
              }),
            ).toHaveCount(0);
          } else if (intent === "focus") {
            await expect(
              page.getByRole("region", {
                name: "Time, control and physical evidence",
                exact: true,
              }),
            ).toBeVisible();
            await expect(
              page.getByLabel("Associated Scenario", { exact: true }),
            ).toBeFocused();
          } else {
            await expect(
              page.getByRole("dialog", {
                name: "Controlled comparison dialog",
                exact: true,
              }),
            ).toBeVisible();
            await expect(
              page.getByLabel("Controlled dialog field"),
            ).toBeFocused();
            await page.keyboard.press("Escape");
          }
        } finally {
          release();
          await page.unrouteAll({ behavior: "wait" });
        }
      });
    }
  });
}
