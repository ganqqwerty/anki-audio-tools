import { readFieldState } from "./field-state-store.js";
import {
  dispatchHtmlAudioSessionEvent,
  readHtmlAudioSessionState,
  stopOtherHtmlAudioSessions,
} from "./html-audio-session-controller.js";
import type {
  HtmlAudioSessionState,
  HtmlAudioStartRequest,
} from "./html-audio-session-machine.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";
import {
  readRepeatPauseSecondsRuntime,
  readTargetDurationMsForVisualizer,
} from "./visualizer-runtime-state.js";

interface SourcePlaybackRequest {
  cursorMs: number;
  endMs: number;
  loop: boolean;
  ord: number;
  regionMode: "full" | "selection";
  repeatPauseMs: number;
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
  const sourceFilename = field.sourceFilename;
  if (!sourceFilename) return false;

  const htmlRequest = htmlAudioStartRequestForSourceRequest(sourceRequest);
  const durationMs = field.graph.durationMs || sourceRequest.endMs;
  stopOtherHtmlAudioSessions(sourceRequest.ord);
  ensureHtmlAudioSessionSource(sourceRequest.ord, sourceFilename, sourceRequest.cursorMs);

  dispatchHtmlAudioStartRequest(htmlRequest, sourceFilename, durationMs);
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
    repeatPauseMs: readRepeatPauseSecondsRuntime(visualizer) * 1000,
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
  request: HtmlAudioStartRequest,
  sourceFilename: string,
  durationMs: number,
): void {
  dispatchHtmlAudioSessionEvent(request.ord, {
    request,
    type: "StartRequested",
  });
  dispatchKnownMetadataForLoadingSource(request.ord, sourceFilename, durationMs);
}

function dispatchKnownMetadataForLoadingSource(
  ord: number,
  sourceFilename: string,
  durationMs: number,
): void {
  if (durationMs <= 0) return;
  const state = readHtmlAudioSessionState(ord);
  if (state.kind === "loading" && state.source.sourceFilename === sourceFilename) {
    dispatchHtmlAudioSessionEvent(ord, {
      durationMs,
      type: "MetadataLoaded",
    });
  }
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

function playbackWarningForVisualizer(visualizer: VisualizerElement): HTMLElement | null {
  return visualizer
    .closest<HTMLElement>(".aqe-controls")
    ?.querySelector<HTMLElement>(".aqe-playback-warning") ?? null;
}
