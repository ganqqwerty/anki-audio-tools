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
import type { VisualizerElement } from "./types.js";

export type SelectionToolbarPreview = "none" | "region" | "rest";

const PLAY_SELECTION_TITLE = "Play selection";
const PAUSE_SELECTION_TITLE = "Pause selection";

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

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
  const busy = anyBusy() || visualizer.dataset.graphBusy === "true";
  const hasTrack = visualizer.dataset.hasTrack === "true";
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
  const playing = visualizer.dataset.playbackState === "playing";
  const title = playing ? PAUSE_SELECTION_TITLE : PLAY_SELECTION_TITLE;
  play.disabled = busy;
  play.dataset.aqeButtonState = playing ? "pause" : "play";
  setButtonTooltipContent(play, title);
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
  setButtonTooltipContent(button, valid ? validTitle : invalidTitle);
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
}
