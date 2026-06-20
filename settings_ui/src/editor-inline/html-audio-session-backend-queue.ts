import { focusAndSendCommand, setPendingPlaybackRequest } from "./bridge.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { updateFieldState } from "./field-state-store.js";
import { logger } from "./logger.js";
import { setPreserveStatusOnPlaybackEndRuntime } from "./visualizer-runtime-state.js";
import type { HtmlAudioStartRequest } from "./html-audio-session-types.js";
import type { PlaybackRequest } from "./types.js";

export function queueBackendPlayback(request: HtmlAudioStartRequest): void {
  const playbackRequest = playbackRequestForHtmlAudioStartRequest(request);
  const visualizer = visualizerForOrd(request.ord);
  if (visualizer) {
    updateFieldState(request.ord, (field) => ({
      ...field,
      playback: { ...field.playback, engine: playbackRequest.engine || "" },
    }));
    setPreserveStatusOnPlaybackEndRuntime(visualizer, request.source === "post_edit");
  }
  setPendingPlaybackRequest(playbackRequest);
  window.__aqeActiveField = request.ord;
  logger.info("playback request queued", playbackRequest);
  focusAndSendCommand(request.ord, "aqe:play");
}

function playbackRequestForHtmlAudioStartRequest(request: HtmlAudioStartRequest): PlaybackRequest {
  const playbackRequest: PlaybackRequest = {
    action: "start",
    cursorMs: request.cursorMs,
    endMs: request.endMs,
    engine: "html",
    loop: request.loop,
    ord: request.ord,
    regionMode: request.regionMode,
  };
  if (request.source === "post_edit" || request.source === "chorusing") {
    playbackRequest.source = request.source;
  }
  return playbackRequest;
}
