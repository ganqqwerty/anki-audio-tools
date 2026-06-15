import { t } from "../lib/i18n.js";
import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { chorusingControlsForVisualizer } from "./chorusing-dom.js";
import { buttonFor } from "./dom-selectors.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { readFieldState } from "./field-state-store.js";
import { isEditorBusy } from "./editor-control-state.js";

export function syncChorusingToolbarButtons(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const controls = chorusingControlsForVisualizer(visualizer);
  const fieldState = readFieldState(ord);
  const hasPlayableTrack = fieldState.graph.hasTrack && readVisualizerTargetDurationMs(visualizer) > 0;
  const busy = isEditorBusy() || fieldState.graph.busy;
  const practiceButton = buttonFor(ord, "aqe:chorusing-practice");
  if (practiceButton) {
    const playing = controls.practiceState === "playing";
    const canInitialize = controls.baseStartMs === null && hasPlayableTrack;
    practiceButton.disabled = busy || !(controls.canPractice || canInitialize);
    practiceButton.dataset.aqeButtonState = playing ? "pause" : "default";
    practiceButton.setAttribute("aria-pressed", playing ? "true" : "false");
    practiceButton.setAttribute("aria-disabled", practiceButton.disabled ? "true" : "false");
    const title = playing
      ? t("editor.command.chorusing_practice.pause_title")
      : t("editor.command.chorusing_practice.title");
    const tooltip = tooltipWithDisabledClarification(
      title,
      practiceButton.disabled
        ? (busy ? t("tooltip.disabled.editor_busy") : t("editor.command.chorusing_practice.disabled_title"))
        : undefined,
    );
    practiceButton.setAttribute("aria-label", tooltip);
    setButtonTooltipContent(practiceButton, tooltip);
  }
  syncChorusingNavButton(
    buttonFor(ord, "aqe:chorusing-previous"),
    controls.canPrevious,
    busy,
    t("editor.command.chorusing_previous.title"),
    t("editor.command.chorusing_previous.disabled_title"),
  );
  syncChorusingNavButton(
    buttonFor(ord, "aqe:chorusing-next"),
    controls.canNext,
    busy,
    t("editor.command.chorusing_next.title"),
    t("editor.command.chorusing_next.disabled_title"),
  );
}

function syncChorusingNavButton(
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
