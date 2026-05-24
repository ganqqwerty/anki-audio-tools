import { allVisualizers, controlsForOrd } from "./dom-selectors.js";
import { t } from "../lib/i18n.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { logger } from "./logger.js";
import type { PlaybackRegion } from "./playback-state.js";
import { selectionForVisualizer } from "./selection-controller.js";
import type { RegionDeleteRequest, VisualizerElement } from "./types.js";
import { isPlaybackState } from "./types.js";

type RegionDeleteOperation = RegionDeleteRequest["operation"];

export interface RegionDeleteAvailability {
  hasSelection: boolean;
  valid: boolean;
  wholeSelection: boolean;
}

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

function regionDeleteButtonForOrd(ord: number): HTMLButtonElement | null {
  return controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-region-button") ?? null;
}

function regionDeleteRestButtonForOrd(ord: number): HTMLButtonElement | null {
  return controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-rest-button") ?? null;
}

function isWholeSelection(region: PlaybackRegion, durationMs: number): boolean {
  return region.startMs <= 0 && region.endMs >= durationMs;
}

function isValidRegionDeleteSelection(region: PlaybackRegion | null, durationMs: number): boolean {
  return !!region && region.endMs > region.startMs && !isWholeSelection(region, durationMs);
}

export function titleForOperation(operation: RegionDeleteOperation, valid: boolean): string {
  if (operation === "delete-rest") {
    return valid ? t("editor.command.delete_rest.title") : t("editor.status.keep_whole_clip");
  }
  return valid ? t("editor.command.delete_region.title") : t("editor.status.delete_whole_clip");
}

function syncRegionDeleteButton(
  button: HTMLButtonElement | null,
  operation: RegionDeleteOperation,
  valid: boolean,
): void {
  if (!button) return;
  button.hidden = !valid;
  button.disabled = anyBusy() || !valid;
  button.dataset.aqeButtonState = valid ? "destructive" : "unavailable";
  setButtonTooltipContent(button, titleForOperation(operation, valid));
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
}

export function regionDeleteAvailabilityFor(visualizer: VisualizerElement): RegionDeleteAvailability {
  const region = selectionForVisualizer(visualizer);
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const wholeSelection = !!region && isWholeSelection(region, durationMs);
  return {
    hasSelection: region !== null,
    valid: isValidRegionDeleteSelection(region, durationMs),
    wholeSelection,
  };
}

export function syncRegionDeleteControl(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const { valid } = regionDeleteAvailabilityFor(visualizer);
  syncRegionDeleteButton(regionDeleteButtonForOrd(ord), "delete-selection", valid);
  syncRegionDeleteButton(regionDeleteRestButtonForOrd(ord), "delete-rest", valid);
}

export function syncAllRegionDeleteControls(): void {
  allVisualizers().forEach(syncRegionDeleteControl);
}

export function regionDeleteRequestFor(
  visualizer: VisualizerElement,
  trigger: RegionDeleteRequest["trigger"],
  operation: RegionDeleteOperation = "delete-selection",
): RegionDeleteRequest | null {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const durationMs = Number(visualizer.dataset.durationMs || "0") || 0;
  const region = selectionForVisualizer(visualizer);
  const availability = regionDeleteAvailabilityFor(visualizer);
  if (!region || !availability.valid) {
    if (region && availability.wholeSelection) {
      logger.warn("region delete rejected whole clip", {
        ord,
        sourceFilename: visualizer.dataset.sourceFilename || "",
        selectionStartMs: region.startMs,
        selectionEndMs: region.endMs,
        durationMs,
        trigger,
        operation,
      });
    }
    return null;
  }
  const sourceFilename = visualizer.dataset.sourceFilename || "";
  if (!sourceFilename) return null;
  const playbackState = visualizer.dataset.playbackState;
  return {
    operation,
    ord,
    sourceFilename,
    selectionStartMs: Math.round(region.startMs),
    selectionEndMs: Math.round(region.endMs),
    cursorMs: Math.round(Number(visualizer.dataset.cursorMs || "0") || 0),
    durationMs: Math.round(durationMs),
    trigger,
    playbackActive: isPlaybackState(playbackState) && playbackState !== "stopped",
  };
}
