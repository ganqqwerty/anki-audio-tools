import {
  allFieldPreferenceNodes,
  allVisualizers,
  fieldPreferenceNodeForOrd,
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

const DELETE_REST_TOOLBAR_TITLE = "Delete audio outside selected region";
const PLAY_SELECTION_TITLE = "Play selection";
const PAUSE_SELECTION_TITLE = "Pause selection";
const FIELD_PREFERENCE_DATASET_KEY = "aqeSelectionToolbarPreferredCollapsed";

const fieldCollapsePreferences = new Map<number, boolean>();

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

function selectionKey(visualizer: VisualizerElement): string {
  return [
    visualizer.dataset.sourceFilename || "",
    visualizer.dataset.selectionStartMs || "",
    visualizer.dataset.selectionEndMs || "",
    visualizer.dataset.durationMs || "",
  ].join("|");
}

function toolbarFor(visualizer: VisualizerElement): HTMLElement | null {
  return visualizer.querySelector<HTMLElement>(".aqe-selection-toolbar");
}

function dotFor(visualizer: VisualizerElement): SVGSVGElement | null {
  return visualizer.querySelector<SVGSVGElement>(".aqe-selection-toolbar-dot");
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
  const dot = dotFor(visualizer);
  const availability = regionDeleteAvailabilityFor(visualizer);
  const busy = anyBusy() || visualizer.dataset.graphBusy === "true";
  const hasTrack = visualizer.dataset.hasTrack === "true";
  const draftActive = draftSelectionForVisualizer(visualizer) !== null;
  const currentSelectionKey = availability.hasSelection ? selectionKey(visualizer) : "";

  if (currentSelectionKey !== visualizer.dataset.selectionToolbarSelectionKey) {
    visualizer.dataset.selectionToolbarCollapsed = preferredCollapsed(visualizer) ? "true" : "false";
    visualizer.dataset.selectionToolbarSelectionKey = currentSelectionKey;
  }

  syncSelectionToolbarButtons(visualizer, busy, availability.valid);
  const available = hasTrack && availability.valid && !draftActive && !busy;
  if (!available) {
    hideToolbar(toolbar, dot);
    setSelectionToolbarPreview(visualizer, "none");
    return;
  }

  const collapsed = visualizer.dataset.selectionToolbarCollapsed === "true";
  if (toolbar) {
    toolbar.hidden = collapsed;
    toolbar.setAttribute("aria-hidden", collapsed ? "true" : "false");
  }
  if (dot) {
    dot.toggleAttribute("hidden", !collapsed);
    dot.setAttribute("tabindex", collapsed ? "0" : "-1");
    dot.setAttribute("aria-hidden", collapsed ? "false" : "true");
    dot.setAttribute("aria-disabled", busy ? "true" : "false");
  }
}

export function syncAllSelectionToolbars(): void {
  allVisualizers().forEach(syncSelectionToolbar);
}

export function collapseSelectionToolbar(visualizer: VisualizerElement): void {
  setPreferredCollapsed(visualizer, true);
  visualizer.dataset.selectionToolbarCollapsed = "true";
  setSelectionToolbarPreview(visualizer, "none");
  syncSelectionToolbar(visualizer);
}

export function expandSelectionToolbar(visualizer: VisualizerElement): void {
  setPreferredCollapsed(visualizer, false);
  visualizer.dataset.selectionToolbarCollapsed = "false";
  syncSelectionToolbar(visualizer);
}

export function collapseSelectionToolbarForOrd(ord: number): void {
  const visualizer = visualizerForOrd(ord);
  if (visualizer) collapseSelectionToolbar(visualizer);
}

export function expandSelectionToolbarForOrd(ord: number): void {
  const visualizer = visualizerForOrd(ord);
  if (visualizer) expandSelectionToolbar(visualizer);
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

export function resetSelectionToolbarPreferences(): void {
  fieldCollapsePreferences.clear();
  allFieldPreferenceNodes().forEach((node) => {
    delete node.dataset[FIELD_PREFERENCE_DATASET_KEY];
  });
}

function hideToolbar(toolbar: HTMLElement | null, dot: SVGSVGElement | null): void {
  if (toolbar) {
    toolbar.hidden = true;
    toolbar.setAttribute("aria-hidden", "true");
  }
  if (dot) {
    dot.setAttribute("hidden", "");
    dot.setAttribute("tabindex", "-1");
    dot.setAttribute("aria-hidden", "true");
    dot.setAttribute("aria-disabled", "true");
  }
}

function preferredCollapsed(visualizer: VisualizerElement): boolean {
  const ord = fieldOrdFor(visualizer);
  if (ord !== null) {
    const fieldPreference = fieldPreferenceForOrd(ord);
    if (fieldPreference !== null) {
      fieldCollapsePreferences.set(ord, fieldPreference);
      visualizer.dataset.selectionToolbarPreferredCollapsed = fieldPreference ? "true" : "false";
      return fieldPreference;
    }
    const storedPreference = fieldCollapsePreferences.get(ord);
    if (storedPreference !== undefined) {
      visualizer.dataset.selectionToolbarPreferredCollapsed = storedPreference ? "true" : "false";
      return storedPreference;
    }
  }
  return visualizer.dataset.selectionToolbarPreferredCollapsed === "true";
}

function setPreferredCollapsed(visualizer: VisualizerElement, collapsed: boolean): void {
  const value = collapsed ? "true" : "false";
  visualizer.dataset.selectionToolbarPreferredCollapsed = value;
  const ord = fieldOrdFor(visualizer);
  if (ord === null) return;
  fieldCollapsePreferences.set(ord, collapsed);
  const fieldNode = fieldPreferenceNodeForOrd(ord);
  if (fieldNode) fieldNode.dataset[FIELD_PREFERENCE_DATASET_KEY] = value;
}

function fieldPreferenceForOrd(ord: number): boolean | null {
  const raw = fieldPreferenceNodeForOrd(ord)?.dataset[FIELD_PREFERENCE_DATASET_KEY];
  if (raw === "true") return true;
  if (raw === "false") return false;
  return null;
}

function fieldOrdFor(visualizer: VisualizerElement): number | null {
  const raw = visualizer.dataset.aqeFieldOrd;
  return raw && /^\d+$/.test(raw) ? Number(raw) : null;
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
    DELETE_REST_TOOLBAR_TITLE,
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
  button.dataset.aqeButtonState = valid ? "default" : "unavailable";
  setButtonTooltipContent(button, valid ? validTitle : invalidTitle);
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
}
