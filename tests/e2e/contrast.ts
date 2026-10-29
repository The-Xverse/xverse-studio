import type { Locator } from "@playwright/test";

/** Selected rendered text, WCAG 2.2 1.4.3 and relative luminance:
 * https://www.w3.org/TR/WCAG22/#contrast-minimum
 * https://www.w3.org/TR/WCAG22/#dfn-relative-luminance
 * Unknown paint/opacity is unsupported, never an assumed white background.
 */
export async function renderedContrast(target: Locator, label: string) {
  return target.evaluate((element, label) => {
    type Color = [number, number, number, number];
    const parse = (text: string): Color | null => {
      const match = text.match(/^rgba?\(([^)]+)\)$/);
      if (!match) return null;
      const parts = match[1].split(/[,\s/]+/).filter(Boolean).map(Number);
      return parts.length >= 3 && parts.every(Number.isFinite)
        ? [parts[0] / 255, parts[1] / 255, parts[2] / 255, parts[3] ?? 1] : null;
    };
    const blend = (front: Color, back: Color): Color => {
      const alpha = front[3] + back[3] * (1 - front[3]);
      return [0, 1, 2].map((i) => (front[i] * front[3] + back[i] * back[3] * (1 - front[3])) / alpha).concat(alpha) as Color;
    };
    const style = getComputedStyle(element), foreground = parse(style.color);
    const base = { label, text: element.textContent?.trim().slice(0, 180), color: style.color,
      fontSize: style.fontSize, fontWeight: style.fontWeight, threshold: 4.5,
      scope: "Selected normal-size rendered text; no overall accessibility certification" };
    for (let node: Element | null = element; node; node = node.parentElement) {
      const paint = getComputedStyle(node);
      if (paint.opacity !== "1" || paint.filter !== "none" || paint.mixBlendMode !== "normal")
        return { ...base, supported: false as const, reason: "Ancestor opacity/filter/blending requires unsupported paint analysis" };
    }
    let background: Color = [0, 0, 0, 0];
    const layers: string[] = [];
    for (let node: Element | null = element; node; node = node.parentElement) {
      const paint = getComputedStyle(node);
      if (paint.backgroundImage !== "none")
        return { ...base, supported: false as const, reason: "Background image/gradient is unsupported", layers };
      const color = parse(paint.backgroundColor);
      if (!color) return { ...base, supported: false as const, reason: "Unsupported background color codec", layers };
      layers.push(paint.backgroundColor);
      if (color[3] > 0) background = blend(background, color);
      if (background[3] >= 0.999999) break;
    }
    if (!foreground || background[3] < 0.999999)
      return { ...base, supported: false as const, reason: "No explicit opaque background or unsupported foreground", layers };
    const observed = blend(foreground, background);
    const luminance = (color: Color) => color.slice(0, 3).map((v) => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4).reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
    const light = luminance(observed), dark = luminance(background);
    const ratio = (Math.max(light, dark) + 0.05) / (Math.min(light, dark) + 0.05);
    return { ...base, supported: true as const, layers, background, compositedForeground: observed, ratio,
      passed: ratio >= 4.5, assumptions: "CSS sRGB colors; alpha composited through explicit backgrounds; no anti-aliasing approximation" };
  }, label);
}
