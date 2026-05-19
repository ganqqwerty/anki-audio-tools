import { processingMessage } from "./commands.js";
import { focusAndSendCommand, setPendingRegionDeleteRequest } from "./bridge.js";
import { logger } from "./logger.js";
import { setControlsBusy, stopProgressClock } from "./actions.js";
import { regionDeleteRequestFor, syncRegionDeleteControl } from "./region-delete-state.js";
import { visualizerForOrd } from "./dom-selectors.js";
import type { RegionDeleteRequest } from "./types.js";

type RegionDeleteOperation = RegionDeleteRequest["operation"];

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

function commandForOperation(operation: RegionDeleteOperation): "aqe:delete-rest" | "aqe:delete-selection" {
  return operation === "delete-rest" ? "aqe:delete-rest" : "aqe:delete-selection";
}

export function sendRegionDelete(
  trigger: RegionDeleteRequest["trigger"],
  node: HTMLElement,
  ord: number,
  operation: RegionDeleteOperation = "delete-selection",
): void {
  if (anyBusy()) return;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  const request = regionDeleteRequestFor(visualizer, trigger, operation);
  syncRegionDeleteControl(visualizer);
  if (!request) return;
  const command = commandForOperation(operation);
  if (typeof node.focus === "function") node.focus();
  stopProgressClock(visualizer, { clearAudio: true });
  setPendingRegionDeleteRequest(request);
  window.__aqeActiveField = ord;
  logger.info("region delete request queued", {
    ord,
    sourceFilename: request.sourceFilename,
    selectionStartMs: request.selectionStartMs,
    selectionEndMs: request.selectionEndMs,
    durationMs: request.durationMs,
    trigger,
    operation,
    playbackActive: request.playbackActive,
  });
  setControlsBusy(ord, true, processingMessage(command));
  focusAndSendCommand(ord, "aqe:delete-selection");
}

export function handleVisualizerKeyDown(event: KeyboardEvent, ord: number): void {
  if (event.key !== "Backspace") return;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || document.activeElement !== visualizer || anyBusy()) return;
  if (!regionDeleteRequestFor(visualizer, "backspace")) {
    syncRegionDeleteControl(visualizer);
    return;
  }
  event.preventDefault();
  sendRegionDelete("backspace", visualizer, ord);
}
