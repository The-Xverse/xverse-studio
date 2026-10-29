import { test, expect, type Page } from "@playwright/test";
import { connectStudio } from "./connect-studio";

async function openExample(page: Page, name: string) {
  const project = await page.evaluate(async (name) => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const r = await fetch("/api/v1/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ name }),
    });
    if (!r.ok) throw Error(await r.text());
    const project = await r.json();
    localStorage.setItem("studio.projectId", project.projectId);
    localStorage.setItem("studio.model.groupByNode", "0");
    return project;
  }, name);
  await page.reload();
  await expect(page.locator(".project-header h1")).toHaveText(name);
  return project;
}

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
])
  test(`model structure: node grouping, keyboard tree and definition drill-down stay presentation-only at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, testInfo) => {
    test.setTimeout(60000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const project = await openExample(
      page,
      `Model structure navigation ${viewport.width}`,
    );
    const writes: string[] = [];
    page.on("request", (r) => {
      if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
        writes.push(r.method() + " " + new URL(r.url()).pathname);
    });
    const toggle = page.getByRole("button", { name: "Group by node" });
    await expect(toggle).toHaveAttribute("aria-pressed", "false");
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-pressed", "true");
    const tree = page.getByRole("tree", { name: "System structure by node" });
    await expect(tree).toBeVisible();
    const groups = tree.locator(":scope > [role=treeitem]");
    await expect(groups).toHaveCount(3);
    await expect(groups.nth(0)).toHaveAccessibleName(
      "controller-node node, controller, 1 members",
    );
    // Keyboard: focus enters on the first item; arrows move, Left/Right collapse/expand.
    await groups.nth(0).focus();
    await page.keyboard.press("ArrowDown");
    await expect(
      tree.getByRole("treeitem", { name: "controller controller" }),
    ).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("heading", { name: "Element inspector" }),
    ).toBeVisible();
    await page.keyboard.press("ArrowLeft");
    await expect(groups.nth(0)).toBeFocused();
    await page.keyboard.press("ArrowLeft");
    await expect(groups.nth(0)).toHaveAttribute("aria-expanded", "false");
    await expect(
      tree.getByRole("treeitem", { name: "controller controller" }),
    ).toHaveCount(0);
    await page.keyboard.press("ArrowRight");
    await expect(groups.nth(0)).toHaveAttribute("aria-expanded", "true");
    await page.keyboard.press("End");
    // A node without instances is listed as its own member.
    await expect(
      tree.getByRole("treeitem", { name: "observer-node observer" }),
    ).toBeFocused();
    await page.keyboard.press("Home");
    await expect(groups.nth(0)).toBeFocused();
    // Select a node: its inspector lists members and declared roles.
    await groups.nth(1).focus();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("heading", { name: "Node inspector" }),
    ).toBeVisible();
    const inspector = page.getByRole("complementary", {
      name: "Element inspector",
    });
    await expect(inspector).toContainText("plant-node");
    await expect(inspector).toContainText("not a deployment target");
    await inspector.getByRole("button", { name: "plant", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Element inspector" }),
    ).toBeVisible();
    // Drill into the Component definition and back up through the breadcrumb.
    await inspector
      .getByRole("button", { name: "Open component definition" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Definition inspector" }),
    ).toBeVisible();
    const breadcrumb = page.getByRole("navigation", { name: "Model location" });
    await expect(breadcrumb).toContainText("reference-loop");
    await expect(breadcrumb).toContainText("plant-node");
    await expect(breadcrumb).toContainText("reference-plant");
    // Below a definition the element step is a link back; elsewhere it is plain text.
    await expect(
      breadcrumb.getByRole("button", { name: "plant", exact: true }),
    ).toBeVisible();
    await expect(inspector).toContainText("state-out");
    await expect(inspector).toContainText("first-order");
    await breadcrumb.getByRole("button", { name: "plant-node" }).click();
    await expect(
      page.getByRole("heading", { name: "Node inspector" }),
    ).toBeVisible();
    // Canvas: one frame per populated node, named ports on elements.
    await expect(page.locator(".node-group-frame")).toHaveCount(3);
    for (const frame of await page.locator(".node-group-frame").all())
      await expect(frame).toBeVisible();

    await expect(page.locator(".node-group-frame").first()).toContainText(
      "controller-node",
    );
    const plantNode = page
      .locator(".element-node")
      .filter({ hasText: "plant-in" });
    await expect(plantNode).toContainText("plant-out");
    // Enabling grouping arranged elements by node: no frame covers a non-member.
    await expect(page.locator(".frame-overlap")).toHaveCount(0);
    await page
      .getByRole("button", { name: "Auto layout", exact: true })
      .click();
    await expect(page.locator(".frame-overlap")).toHaveCount(0);
    // Search narrows the grouped tree to matching members and their node.
    await page.getByLabel("Search elements").fill("plant");
    await expect(tree.locator(":scope > [role=treeitem]")).toHaveCount(1);
    await expect(
      tree.getByRole("treeitem", { name: "plant plant" }),
    ).toBeVisible();
    await page.getByLabel("Search elements").fill("");
    // Navigation changed nothing executable; saving layout stores elements only.
    expect(writes).toEqual([]);
    await page
      .getByRole("button", { name: "Save layout", exact: true })
      .click();
    await expect(
      page.getByText("Layout saved separately from executable XDL."),
    ).toBeVisible();
    const saved = await page.request
      .get(`/api/v1/projects/${project.projectId}`)
      .then((r) => r.json());
    expect(saved.revision).toBe(project.revision);
    // Saved positions are exactly the element references; frames are never stored.
    expect(Object.keys(saved.layout.positions).sort()).toEqual(
      ["controller", "observer-node", "plant"].map(
        (id) =>
          "xdl://org.xverse.studio.process-control/system/reference-loop#" + id,
      ),
    );
    await page.screenshot({
      path: testInfo.outputPath(`model-structure-${viewport.width}.png`),
    });
  });
