import {
  allVisualizers,
  visualizerForOrd,
} from "./dom-selectors.js";
import { t } from "../lib/i18n.js";
import { draftSelectionForVisualizer } from "./selection-controller.js";
import {
  regionDeleteAvailabilityFor,
  titleForOperation,
} from "./region-delete-state.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { buttonTooltipContent, tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
import type { VisualizerElement } from "./types.js";
import { readFieldState } from "./field-state-store.js";
import { isEditorBusy } from "./editor-control-state.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

export type SelectionToolbarPreview = "none" | "region" | "rest";

const PLAY_SELECTION_TITLE = "Play selection";
const PAUSE_SELECTION_TITLE = "Pause selection";

function toolbarFor(visualizer: VisualizerElement): HTMLElement | null {
  return visualizer.querySelector<HTMLElement>(".aqe-selection-toolbar");
}

function playButtonFor(visualizer: VisualizerElement): HTMLButtonElement | null {
  return visualizer.querySelector<HTMLButtonElement>(".aqe-selection-toolbar-play");
}

function deleteRegionButtonFor(visualizer: VisualizerElement): HTMLButtonElement | null {
  return visualizer.querySelector<HTMLButtonElement>(".aqe-delete-region-button");
}

function deleteRestButtonFor(visualizer: VisualizerElement): HTMLButtonElement | null {
  return visualizer.querySelector<HTMLButtonElement>(".aqe-delete-rest-button");
}

export function syncSelectionToolbar(visualizer: VisualizerElement): void {
  const toolbar = toolbarFor(visualizer);
  const availability = regionDeleteAvailabilityFor(visualizer);
  const s = readFieldState(fieldOrd(visualizer));
  const busy = isEditorBusy() || s.graph.busy;
  const hasTrack = s.graph.hasTrack;
  const draftActive = draftSelectionForVisualizer(visualizer) !== null;

  syncSelectionToolbarButtons(visualizer, busy, availability.valid);
  const available = hasTrack && availability.hasSelection && !draftActive && !busy;
  if (!available) {
    hideToolbar(toolbar);
    setSelectionToolbarPreview(visualizer, "none");
    return;
  }

  if (toolbar) {
    toolbar.hidden = false;
    toolbar.setAttribute("aria-hidden", "false");
  }
}

export function syncAllSelectionToolbars(): void {
  allVisualizers().forEach(syncSelectionToolbar);
}

export function setSelectionToolbarPreview(
  visualizer: VisualizerElement,
  preview: SelectionToolbarPreview,
): void {
  visualizer.dataset.selectionToolbarPreview = preview;
}

export function setSelectionToolbarPreviewForOrd(ord: number, preview: SelectionToolbarPreview): void {
  const visualizer = visualizerForOrd(ord);
  if (visualizer) setSelectionToolbarPreview(visualizer, preview);
}

function hideToolbar(toolbar: HTMLElement | null): void {
  if (toolbar) {
    toolbar.hidden = true;
    toolbar.setAttribute("aria-hidden", "true");
  }
}

function syncSelectionToolbarButtons(
  visualizer: VisualizerElement,
  busy: boolean,
  validDeleteSelection: boolean,
): void {
  syncToolbarPlayButton(visualizer, busy);
  syncToolbarDeleteButton(
    deleteRegionButtonFor(visualizer),
    validDeleteSelection,
    busy,
    t("editor.command.delete_region.title"),
    titleForOperation("delete-selection", false),
  );
  syncToolbarDeleteButton(
    deleteRestButtonFor(visualizer),
    validDeleteSelection,
    busy,
    t("editor.command.delete_rest.title"),
    titleForOperation("delete-rest", false),
  );
}

function syncToolbarPlayButton(visualizer: VisualizerElement, busy: boolean): void {
  const play = playButtonFor(visualizer);
  if (!play) return;
  const playing = readFieldState(fieldOrd(visualizer)).playback.state === "playing";
  const title = playing ? PAUSE_SELECTION_TITLE : PLAY_SELECTION_TITLE;
  const label = playing ? t("editor.command.pause.label") : t("editor.command.play.label");
  play.disabled = busy;
  play.dataset.aqeButtonState = playing ? "pause" : "play";
  setButtonTooltipContent(
    play,
    tooltipWithDisabledClarification(
      buttonTooltipContent(label, title),
      busy ? t("tooltip.disabled.editor_busy") : undefined,
    ),
  );
  play.setAttribute("aria-disabled", play.disabled ? "true" : "false");
}

function syncToolbarDeleteButton(
  button: HTMLButtonElement | null,
  valid: boolean,
  busy: boolean,
  validTitle: string,
  invalidTitle: string,
): void {
  if (!button) return;
  button.hidden = !valid;
  button.disabled = busy || !valid;
  button.dataset.aqeButtonState = valid ? "destructive" : "unavailable";
  const reason = busy && valid ? t("tooltip.disabled.editor_busy") : (!valid ? invalidTitle : undefined);
  const enabledTitle = button.dataset.aqeEnabledTitle || validTitle;
  setButtonTooltipContent(button, tooltipWithDisabledClarification(enabledTitle, reason));
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
}
