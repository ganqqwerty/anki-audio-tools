import { focusAndSendCommand, setPendingPlaybackRequest } from "./bridge.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { updateFieldState } from "./field-state-store.js";
import { logger } from "./logger.js";
import type { PlaybackRequest } from "./types.js";
import { setPreserveStatusOnPlaybackEndRuntime } from "./visualizer-runtime-state.js";

export function sendPlaybackRequest(request: PlaybackRequest): void {
  const visualizer = visualizerForOrd(request.ord);
  if (visualizer) {
    updateFieldState(request.ord, (state) => ({
      ...state,
      playback: { ...state.playback, engine: request.engine || "" },
    }));
    setPreserveStatusOnPlaybackEndRuntime(visualizer, request.source === "post_edit");
  }
  setPendingPlaybackRequest(request);
  window.__aqeActiveField = request.ord;
  logger.info("playback request queued", request);
  focusAndSendCommand(request.ord, "aqe:play");
}
