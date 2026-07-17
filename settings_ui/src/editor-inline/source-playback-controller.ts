import { readFieldState } from "./field-state-store.js";
import { currentAudioSourceForOrd } from "./dom-selectors.js";
import {
  dispatchHtmlAudioSessionEvent,
  readHtmlAudioSessionState,
} from "./html-audio-session-controller.js";
import { clearPlaybackWarning } from "./control-status-renderer.js";
import { logger } from "./logger.js";
import { startEditorPlaybackPractice } from "./editor-practice-controller.js";
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
  source: "user" | "post_edit";
}

export function startSourceHtmlPlayback(
  visualizer: VisualizerElement,
  request: PlaybackRequest,
): boolean {
  clearPlaybackWarning(request.ord);
  const sourceRequest = sourcePlaybackRequestFor(visualizer, request);
  const field = readFieldState(sourceRequest.ord);
  const sourceFilename = sourceSessionFilename(sourceRequest.ord)
    || field.sourceFilename
    || currentAudioSourceForOrd(sourceRequest.ord);
  if (!sourceFilename) return false;

  const htmlRequest = htmlAudioStartRequestForSourceRequest(sourceRequest);
  const durationMs = field.graph.durationMs || sourceRequest.endMs;
  logger.debug("source_html_playback.start", {
    durationMs,
    request: htmlAudioStartRequestForSourceRequest(sourceRequest),
    session: htmlAudioSourceSessionSummary(readHtmlAudioSessionState(sourceRequest.ord)),
    sourceFilename,
  });
  ensureHtmlAudioSessionSource(sourceRequest.ord, sourceFilename, sourceRequest.cursorMs);

  startEditorPlaybackPractice(visualizer, htmlRequest);
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

function htmlAudioSessionNeedsSource(
  state: HtmlAudioSessionState,
  sourceFilename: string,
): boolean {
  if (state.kind === "empty" || state.kind === "failed") return true;
  if (state.source.kind !== "source") return true;
  if (state.source.sourceFilename !== sourceFilename) return true;
  return false;
}

function sourceSessionFilename(ord: number): string {
  const state = readHtmlAudioSessionState(ord);
  if (state.kind === "empty" || state.kind === "failed") return "";
  return state.source.kind === "source" ? state.source.sourceFilename : "";
}

function htmlAudioSourceSessionSummary(state: HtmlAudioSessionState): Record<string, unknown> {
  return {
    kind: state.kind,
    sourceFilename: "source" in state ? state.source?.sourceFilename : null,
  };
}
