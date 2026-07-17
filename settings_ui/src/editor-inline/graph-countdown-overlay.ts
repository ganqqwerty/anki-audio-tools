import { t } from "../lib/i18n.js";
import type { VisualizerElement } from "./types.js";

class CountdownOverlayRuntime {
  readonly repeatPauseTimers = new Map<VisualizerElement, number>();

  dispose(): void {
    for (const timer of this.repeatPauseTimers.values()) window.clearTimeout(timer);
    this.repeatPauseTimers.clear();
  }
}

let activeRuntime: CountdownOverlayRuntime | null = null;

function overlayRuntime(): CountdownOverlayRuntime {
  activeRuntime ??= new CountdownOverlayRuntime();
  return activeRuntime;
}

export function renderGraphCountdownOverlay(
  visualizer: VisualizerElement,
  seconds: number,
  ariaLabel: string,
): void {
  const overlay = visualizer.querySelector<HTMLElement>(".aqe-graph-countdown-overlay");
  if (!overlay) return;
  const valueNode = overlay.querySelector<HTMLElement>(".aqe-graph-countdown-value");
  overlay.hidden = false;
  overlay.setAttribute("aria-label", ariaLabel);
  if (valueNode) valueNode.textContent = String(seconds);
}

export function clearGraphCountdownOverlay(visualizer: VisualizerElement): void {
  const overlay = visualizer.querySelector<HTMLElement>(".aqe-graph-countdown-overlay");
  if (!overlay) return;
  const valueNode = overlay.querySelector<HTMLElement>(".aqe-graph-countdown-value");
  overlay.hidden = true;
  overlay.removeAttribute("aria-label");
  if (valueNode) valueNode.textContent = "";
}

export function startRepeatPauseCountdownOverlay(visualizer: VisualizerElement, delayMs: number): void {
  clearRepeatPauseCountdownOverlay(visualizer);
  let remainingSeconds = Math.ceil(Math.max(0, delayMs) / 1000);
  const tick = (): void => {
    if (remainingSeconds <= 0) {
      clearRepeatPauseCountdownOverlay(visualizer);
      return;
    }
    renderGraphCountdownOverlay(
      visualizer,
      remainingSeconds,
      t("editor.playback.repeat_countdown", { seconds: remainingSeconds }),
    );
    remainingSeconds -= 1;
    const timer = window.setTimeout(tick, 1000);
    overlayRuntime().repeatPauseTimers.set(visualizer, timer);
  };
  tick();
}

export function clearRepeatPauseCountdownOverlay(visualizer: VisualizerElement): void {
  const timer = overlayRuntime().repeatPauseTimers.get(visualizer);
  if (timer !== undefined) {
    window.clearTimeout(timer);
    overlayRuntime().repeatPauseTimers.delete(visualizer);
  }
  clearGraphCountdownOverlay(visualizer);
}

export function disposeGraphCountdownOverlays(): void {
  activeRuntime?.dispose();
  activeRuntime = null;
}
