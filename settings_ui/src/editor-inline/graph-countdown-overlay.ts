import { t } from "../lib/i18n.js";
import type { VisualizerElement } from "./types.js";

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
    visualizer.__aqeRepeatPauseOverlayTimer = window.setTimeout(tick, 1000);
  };
  tick();
}

export function clearRepeatPauseCountdownOverlay(visualizer: VisualizerElement): void {
  if (visualizer.__aqeRepeatPauseOverlayTimer) {
    window.clearTimeout(visualizer.__aqeRepeatPauseOverlayTimer);
    visualizer.__aqeRepeatPauseOverlayTimer = null;
  }
  clearGraphCountdownOverlay(visualizer);
}
