import { t } from "../lib/i18n.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { backChainingControlsForVisualizer } from "./back-chaining-dom.js";
import { buttonFor } from "./dom-selectors.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";

export function syncBackChainingToolbarButtons(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const controls = backChainingControlsForVisualizer(visualizer);
  const hasPlayableTrack = visualizer.dataset.hasTrack === "true" && readVisualizerTargetDurationMs(visualizer) > 0;
  const busy = document.body.dataset.aqeBusy === "true" || visualizer.dataset.graphBusy === "true";
  const practiceButton = buttonFor(ord, "aqe:back-chain-practice");
  if (practiceButton) {
    const playing = controls.practiceState === "playing";
    const canInitialize = controls.baseStartMs === null && hasPlayableTrack;
    practiceButton.disabled = busy || !(controls.canPractice || canInitialize);
    practiceButton.dataset.aqeButtonState = playing ? "pause" : "default";
    practiceButton.setAttribute("aria-pressed", playing ? "true" : "false");
    practiceButton.setAttribute("aria-disabled", practiceButton.disabled ? "true" : "false");
    const title = playing
      ? t("editor.command.back_chain_practice.pause_title")
      : t("editor.command.back_chain_practice.title");
    practiceButton.setAttribute("aria-label", title);
    setButtonTooltipContent(practiceButton, title);
  }
  syncBackChainingNavButton(buttonFor(ord, "aqe:back-chain-previous"), controls.canPrevious, busy, t("editor.command.back_chain_previous.title"));
  syncBackChainingNavButton(buttonFor(ord, "aqe:back-chain-next"), controls.canNext, busy, t("editor.command.back_chain_next.title"));
}

function syncBackChainingNavButton(
  button: HTMLButtonElement | null,
  canUse: boolean,
  busy: boolean,
  title: string,
): void {
  if (!button) return;
  button.disabled = busy || !canUse;
  button.dataset.aqeButtonState = canUse ? "default" : "unavailable";
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
  setButtonTooltipContent(button, title);
}
