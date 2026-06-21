import { readFieldState } from "./field-state-store.js";
import { currentAudioSourceForOrd } from "./dom-selectors.js";
import {
  dispatchHtmlAudioSessionEvent,
  htmlAudioSessionSourceFilename,
  readHtmlAudioSessionState,
  stopOtherHtmlAudioSessions,
} from "./html-audio-session-controller.js";
import { htmlAudioReadinessFor } from "./audio-readiness.js";
import { logger } from "./logger.js";
import type {
  HtmlAudioSessionState,
  HtmlAudioStartRequest,
} from "./html-audio-session-machine.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";
import { readTargetDurationMsForVisualizer } from "./visualizer-runtime-state.js";

interface SourcePlaybackRequest {
  cursorMs: number;
  endMs: number;
  loop: boolean;
  ord: number;
  regionMode: "full" | "selection";
  resetCursorMs: number;
  source: "user" | "post_edit" | "chorusing";
}

export function startSourceHtmlPlayback(
  visualizer: VisualizerElement,
  request: PlaybackRequest,
): boolean {
  clearPostEditPlaybackWarning(visualizer);
  const sourceRequest = sourcePlaybackRequestFor(visualizer, request);
  const field = readFieldState(sourceRequest.ord);
  const sourceFilename = htmlAudioSessionSourceFilename(sourceRequest.ord)
    || currentAudioSourceForOrd(sourceRequest.ord)
    || field.sourceFilename;
  if (!sourceFilename) return false;

  const htmlRequest = htmlAudioStartRequestForSourceRequest(sourceRequest);
  const durationMs = field.graph.durationMs || sourceRequest.endMs;
  logger.debug("source_html_playback.start", {
    durationMs,
    readiness: htmlAudioReadinessFor(visualizer),
    request: htmlAudioStartRequestForSourceRequest(sourceRequest),
    session: htmlAudioSourceSessionSummary(readHtmlAudioSessionState(sourceRequest.ord)),
    sourceFilename,
  });
  stopOtherHtmlAudioSessions(sourceRequest.ord);
  ensureHtmlAudioSessionSource(sourceRequest.ord, sourceFilename, sourceRequest.cursorMs);

  dispatchHtmlAudioStartRequest(visualizer, htmlRequest, sourceFilename, durationMs);
  return true;
}

function sourcePlaybackRequestFor(
  visualizer: VisualizerElement,
  request: PlaybackRequest,
): SourcePlaybackRequest {
  const regionMode = request.regionMode ?? "full";
  return {
    cursorMs: request.cursorMs,
    endMs: request.endMs ?? readTargetDurationMsForVisualizer(visualizer, 0),
    loop: request.loop === true,
    ord: request.ord,
    regionMode,
    resetCursorMs: resetCursorMsForPlaybackRequest(request.ord, regionMode, request.cursorMs),
    source: request.source ?? "user",
  };
}

function htmlAudioStartRequestForSourceRequest(
  request: SourcePlaybackRequest,
): HtmlAudioStartRequest {
  return {
    cursorMs: request.cursorMs,
    endMs: request.endMs,
    loop: request.loop,
    ord: request.ord,
    regionMode: request.regionMode,
    resetCursorMs: request.resetCursorMs,
    source: request.source,
  };
}

function resetCursorMsForPlaybackRequest(
  ord: number,
  regionMode: "full" | "selection",
  fallbackMs: number,
): number {
  const field = readFieldState(ord);
  if (regionMode === "selection" && field.selection.startMs !== null) {
    return Math.round(field.selection.startMs);
  }
  if (regionMode === "full") {
    return Math.round(field.cursor.anchorMs);
  }
  return Math.round(fallbackMs);
}

function ensureHtmlAudioSessionSource(
  ord: number,
  sourceFilename: string,
  cursorMs: number,
): void {
  const state = readHtmlAudioSessionState(ord);
  if (!htmlAudioSessionNeedsSource(state, sourceFilename)) return;
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs,
    source: { kind: "source", sourceFilename },
    type: "SourceConfigured",
  });
}

function dispatchHtmlAudioStartRequest(
  visualizer: VisualizerElement,
  request: HtmlAudioStartRequest,
  sourceFilename: string,
  durationMs: number,
): void {
  dispatchHtmlAudioSessionEvent(request.ord, {
    request,
    type: "StartRequested",
  });
  if (htmlAudioReadinessFor(visualizer).failed) {
    dispatchHtmlAudioSessionEvent(request.ord, {
      cursorMs: request.cursorMs,
      reason: "audio_error",
      type: "AudioError",
    });
    return;
  }
  dispatchKnownMetadataForLoadingSource(request.ord, sourceFilename, durationMs);
}

function dispatchKnownMetadataForLoadingSource(
  ord: number,
  sourceFilename: string,
  durationMs: number,
): void {
  if (durationMs <= 0) {
    logger.debug("source_html_playback.metadata_known_skipped", {
      durationMs,
      ord,
      reason: "non_positive_duration",
      sourceFilename,
    });
    return;
  }
  const state = readHtmlAudioSessionState(ord);
  if (state.kind === "loading" && state.source.sourceFilename === sourceFilename) {
    logger.debug("source_html_playback.metadata_known_dispatched", {
      durationMs,
      ord,
      sourceFilename,
    });
    dispatchHtmlAudioSessionEvent(ord, {
      durationMs,
      type: "MetadataLoaded",
    });
    return;
  }
  logger.debug("source_html_playback.metadata_known_skipped", {
    durationMs,
    ord,
    reason: state.kind === "loading" ? "source_mismatch" : "state_not_loading",
    session: htmlAudioSourceSessionSummary(state),
    sourceFilename,
  });
}

function htmlAudioSessionNeedsSource(
  state: HtmlAudioSessionState,
  sourceFilename: string,
): boolean {
  if (state.kind === "empty" || state.kind === "failed") return true;
  if (state.source.sourceFilename !== sourceFilename) return true;
  return state.kind !== "ready" && state.kind !== "loading";
}

function clearPostEditPlaybackWarning(visualizer: VisualizerElement): void {
  const warning = playbackWarningForVisualizer(visualizer);
  if (!warning) return;
  warning.textContent = "";
  delete warning.dataset.kind;
  warning.hidden = true;
}

function htmlAudioSourceSessionSummary(state: HtmlAudioSessionState): Record<string, unknown> {
  return {
    kind: state.kind,
    sourceFilename: "source" in state ? state.source?.sourceFilename : null,
  };
}

function playbackWarningForVisualizer(visualizer: VisualizerElement): HTMLElement | null {
  return visualizer
    .closest<HTMLElement>(".aqe-controls")
    ?.querySelector<HTMLElement>(".aqe-playback-warning") ?? null;
}
