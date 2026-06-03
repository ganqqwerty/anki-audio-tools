import { t } from "../lib/i18n.js";
import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
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
    const tooltip = tooltipWithDisabledClarification(
      title,
      practiceButton.disabled
        ? (busy ? t("tooltip.disabled.editor_busy") : t("editor.command.back_chain_practice.disabled_title"))
        : undefined,
    );
    practiceButton.setAttribute("aria-label", tooltip);
    setButtonTooltipContent(practiceButton, tooltip);
  }
  syncBackChainingNavButton(
    buttonFor(ord, "aqe:back-chain-previous"),
    controls.canPrevious,
    busy,
    t("editor.command.back_chain_previous.title"),
    t("editor.command.back_chain_previous.disabled_title"),
  );
  syncBackChainingNavButton(
    buttonFor(ord, "aqe:back-chain-next"),
    controls.canNext,
    busy,
    t("editor.command.back_chain_next.title"),
    t("editor.command.back_chain_next.disabled_title"),
  );
}

function syncBackChainingNavButton(
  button: HTMLButtonElement | null,
  canUse: boolean,
  busy: boolean,
  title: string,
  disabledReason: string,
): void {
  if (!button) return;
  button.disabled = busy || !canUse;
  button.dataset.aqeButtonState = canUse ? "default" : "unavailable";
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
  const tooltip = tooltipWithDisabledClarification(
    title,
    button.disabled ? (busy ? t("tooltip.disabled.editor_busy") : disabledReason) : undefined,
  );
  setButtonTooltipContent(button, tooltip);
}
