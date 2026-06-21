import { projectRepeatEnabled } from "./repeat-control-projection.js";
import { htmlAudioReadinessFor } from "./audio-readiness.js";
import { anyBusy } from "./control-actions.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { readFieldState } from "./field-state-store.js";
import { logger } from "./logger.js";
import {
  logPlaybackReadinessDecision,
  playbackReadinessDecisionFor,
  postEditPlaybackStartContext,
} from "./playback-telemetry.js";
import {
  consumePostEditPlaybackIntent,
  postEditRenderedGraphCanDriveHtmlPlayback,
} from "./post-edit-playback.js";
import { effectivePlaybackRegion } from "./selection-controller.js";
import { startSourcePlaybackAction } from "./source-playback-actions.js";
import type { PlaybackRequest } from "./types.js";
import { setRepeatPauseSecondsRuntime } from "./visualizer-runtime-state.js";

export function playAfterEdit(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) {
    logger.warn("post-edit playback start rejected: visualizer missing", { ord });
    return false;
  }
  if (anyBusy()) {
    logger.info("post-edit playback start rejected: editor busy", postEditPlaybackStartContext(ord, visualizer));
    return false;
  }
  const readiness = htmlAudioReadinessFor(visualizer);
  if (readiness.transient && !postEditRenderedGraphCanDriveHtmlPlayback(
    ord,
    readFieldState(ord).sourceFilename,
    readiness,
  )) {
    logger.info("post-edit playback start rejected: browser audio loading", {
      ...postEditPlaybackStartContext(ord, visualizer),
      htmlAudioReadinessReason: readiness.reason,
      htmlAudioReadinessState: readiness.state,
    });
    return false;
  }
  const intent = consumePostEditPlaybackIntent(ord);
  if (intent) {
    setRepeatPauseSecondsRuntime(visualizer, intent.repeatPauseSeconds);
    projectRepeatEnabled(visualizer, intent.repeat);
  }
  window.__aqeActiveField = ord;
  const region = effectivePlaybackRegion(visualizer);
  const decision = playbackReadinessDecisionFor(visualizer);
  const request: PlaybackRequest = {
    action: "start",
    cursorMs: Math.round(region.startMs),
    endMs: Math.round(region.endMs),
    engine: decision.engine,
    loop: readFieldState(ord).playback.repeat,
    ord,
    regionMode: region.mode,
    source: "post_edit",
  };
  logPlaybackReadinessDecision("post_edit", visualizer, decision, {
    action: request.action,
    endMs: request.endMs ?? null,
    source: "post_edit",
  });
  logger.info("post-edit playback start requested", {
    ...postEditPlaybackStartContext(ord, visualizer),
    cursorMs: request.cursorMs,
    endMs: request.endMs,
    loop: request.loop,
    regionMode: request.regionMode,
  });
  const started = startSourcePlaybackAction(visualizer, request);
  logger.info("post-edit html playback start result", {
    ...postEditPlaybackStartContext(ord, visualizer),
    started,
  });
  return started;
}
