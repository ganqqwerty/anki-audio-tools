import { allVisualizers, controlsForOrd } from "./dom-selectors.js";
import { logger } from "./logger.js";
import type { PlaybackRegion } from "./playback-state.js";
import { selectionForVisualizer } from "./selection-controller.js";
import type { RegionDeleteRequest, VisualizerElement } from "./types.js";
import { isPlaybackState } from "./types.js";

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

function regionDeleteButtonForOrd(ord: number): HTMLButtonElement | null {
  return controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-region-button") ?? null;
}

function isWholeSelection(region: PlaybackRegion, durationMs: number): boolean {
  return region.startMs <= 0 && region.endMs >= durationMs;
}

function isValidRegionDeleteSelection(region: PlaybackRegion | null, durationMs: number): boolean {
  return !!region && region.endMs > region.startMs && !isWholeSelection(region, durationMs);
}

export function syncRegionDeleteControl(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const button = regionDeleteButtonForOrd(ord);
  if (!button) return;
  const region = selectionForVisualizer(visualizer);
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const hasSelection = region !== null;
  const valid = isValidRegionDeleteSelection(region, durationMs);
  button.hidden = !hasSelection;
  button.disabled = anyBusy() || !valid;
  button.dataset.aqeButtonState = valid ? "default" : "unavailable";
  button.title = valid ? "Delete selected region" : "Cannot delete the whole audio clip";
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
}

export function syncAllRegionDeleteControls(): void {
  allVisualizers().forEach(syncRegionDeleteControl);
}

export function regionDeleteRequestFor(
  visualizer: VisualizerElement,
  trigger: RegionDeleteRequest["trigger"],
): RegionDeleteRequest | null {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const durationMs = Number(visualizer.dataset.durationMs || "0") || 0;
  const region = selectionForVisualizer(visualizer);
  if (!region || !isValidRegionDeleteSelection(region, durationMs)) {
    if (region && isWholeSelection(region, durationMs)) {
      logger.warn("region delete rejected whole clip", {
        ord,
        sourceFilename: visualizer.dataset.sourceFilename || "",
        selectionStartMs: region.startMs,
        selectionEndMs: region.endMs,
        durationMs,
        trigger,
      });
    }
    return null;
  }
  const sourceFilename = visualizer.dataset.sourceFilename || "";
  if (!sourceFilename) return null;
  const playbackState = visualizer.dataset.playbackState;
  return {
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
