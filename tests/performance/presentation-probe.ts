import type { Page } from "@playwright/test";

/** Passive timestamps: delegates all real input and HTTP to the existing journey. */
export async function beginPresentationProbe(page: Page, projectId: string, start: number) {
  await page.evaluate(({ projectId, start }) => {
    const state = window as any;
    state.__studioPresentationProbe?.stop();
    performance.setResourceTimingBufferSize(4096);
    const data: any = { start, graphPresentedAt: null, validationClickedAt: null, validationPresentedAt: null, requests: [] };
    let graphPending = false, validationPending = false;
    const validationUrl = location.origin + `/api/v1/projects/${projectId}/validations`;
    const button = () => [...document.querySelectorAll<HTMLButtonElement>("button")].find((b) => b.textContent?.trim() === "Validate");
    const graphReady = () => {
      const control = button();
      if (!control || control.disabled || document.querySelectorAll(".tree-list button").length !== 200 || document.querySelectorAll(".react-flow__node-element").length !== 200 || document.querySelectorAll(".react-flow__edge").length !== 400) return false;
      const rect = control.getBoundingClientRect();
      const hit = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
      return hit?.closest("button") === control;
    };
    const validationReady = () => data.validationClickedAt !== null &&
      [...performance.getEntriesByName(validationUrl)].some((e) => e.startTime >= start && (e as PerformanceResourceTiming).responseEnd > 0) &&
      document.querySelector(".alerts")?.textContent?.includes("Authoritative platform validation passed");
    const inspect = () => {
      if (data.graphPresentedAt === null && !graphPending && graphReady()) {
        graphPending = true;
        requestAnimationFrame(() => requestAnimationFrame(() => {
          if (graphReady()) data.graphPresentedAt = performance.now();
          graphPending = false;
        }));
      }
      if (data.validationPresentedAt === null && !validationPending && validationReady()) {
        validationPending = true;
        requestAnimationFrame(() => requestAnimationFrame(() => {
          if (validationReady()) data.validationPresentedAt = performance.now();
          validationPending = false;
        }));
      }
    };
    const click = (event: MouseEvent) => {
      if ((event.target as Element)?.closest("button") === button()) {
        data.validationClickedAt = performance.now();
        data.validationClickTrusted = event.isTrusted;
      }
    };
    const mutations = new MutationObserver(inspect);
    mutations.observe(document.body, { childList: true, subtree: true, characterData: true });
    const resources = new PerformanceObserver(inspect);
    resources.observe({ type: "resource" });
    document.addEventListener("click", click, true);
    state.__studioPresentationProbe = { data, stop: () => {
      mutations.disconnect(); resources.disconnect(); document.removeEventListener("click", click, true);
      data.requests = (performance.getEntriesByType("resource") as PerformanceResourceTiming[])
        .filter((e) => e.startTime >= start && new URL(e.name).pathname.startsWith(`/api/v1/projects/${projectId}`))
        .map((e) => ({ path: new URL(e.name).pathname, start: e.startTime, responseStart: e.responseStart, responseEnd: e.responseEnd, duration: e.duration }));
    } };
  }, { projectId, start });
}

export async function endPresentationProbe(page: Page, end: number) {
  return page.evaluate((end) => {
    const state = (window as any).__studioPresentationProbe;
    state.stop();
    const d = state.data;
    return { ...d, driverEnd: end,
      graphPresentationMilliseconds: d.graphPresentedAt === null ? null : d.graphPresentedAt - d.start,
      validationPresentationMilliseconds: d.validationPresentedAt === null ? null : d.validationPresentedAt - d.validationClickedAt,
      waitingBetweenActionsMilliseconds: d.graphPresentedAt === null ? null : d.validationClickedAt - d.graphPresentedAt,
      waitingAfterPresentationMilliseconds: d.validationPresentedAt === null ? null : end - d.validationPresentedAt };
  }, end);
}
