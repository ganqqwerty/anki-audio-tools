import {
  allVisualizers,
} from "./dom-selectors.js";
import {
  audioClockReady as isAudioClockReady,
  fieldPlaybackUsesAudioClock,
  installAudioClockHandlers as installAudioClockElementHandlers,
  resetAudioClockState as resetAudioClockElementState,
} from "./audio-clock.js";
import { logger } from "./logger.js";
import {
  dispatchHtmlAudioSessionEvent,
  readHtmlAudioSessionState,
  setHtmlAudioSourceBoundaryHandler,
} from "./html-audio-session-controller.js";
import type { HtmlAudioStartRequest } from "./html-audio-session-machine.js";
import { handleSelectedRepeatAutoAdvanceBoundary } from "./selection-auto-advance-controller.js";
import { completePlayback, playbackStateFor, startProgressClock, stopProgressClock } from "./playback-actions.js";
import { renderCursor } from "./visualizer-renderer.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
import type { PlaybackPass } from "./playback-model.js";
import type { VisualizerElement } from "./types.js";
import { readFieldState, updateFieldState } from "./field-state-store.js";
import {
  projectRepeatEnabled,
  repeatEnabledFor,
} from "./repeat-control-projection.js";
import {
  isRepeatPauseWaitingRuntime,
  readRepeatPauseSecondsRuntime,
  readTargetDurationMsForVisualizer,
  preserveStatusOnPlaybackEndRuntime,
  setTargetDurationMsForVisualizer,
} from "./visualizer-runtime-state.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

export function stopOtherPlayback(activeVisualizer: VisualizerElement): void {
  for (const visualizer of allVisualizers()) {
    if (visualizer !== activeVisualizer && playbackStateFor(visualizer) !== "stopped") {
      stopProgressClock(visualizer);
    }
  }
}

export function resetAudioClockState(visualizer: VisualizerElement): void {
  resetAudioClockElementState(visualizer);
}

export function pauseAudioClock(visualizer: VisualizerElement): void {
  const ord = fieldOrd(visualizer);
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs: readFieldState(ord).cursor.ms,
    type: "StopRequested",
  });
}

export function clearAudioClockSource(visualizer: VisualizerElement): void {
  dispatchHtmlAudioSessionEvent(fieldOrd(visualizer), { type: "SourceCleared" });
}

export function configureAudioClock(visualizer: VisualizerElement, filename: string, cursorMs?: number): void {
  const ord = fieldOrd(visualizer);
  if (!filename) {
    clearAudioClockSource(visualizer);
    return;
  }
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs: cursorMs ?? readFieldState(ord).cursor.ms,
    source: { kind: "source", sourceFilename: filename },
    type: "SourceConfigured",
  });
}

export function installAudioClockHandlers(visualizer: VisualizerElement): void {
  setHtmlAudioSourceBoundaryHandler(handleHtmlAudioSourceBoundary);
  installAudioClockElementHandlers(visualizer, {
    onLoadedMetadata(durationMs) {
      if (readFieldState(fieldOrd(visualizer)).graph.hasTrack) return;
      const ord = fieldOrd(visualizer);
      updateFieldState(ord, (s) => ({
        ...s,
        graph: { ...s.graph, durationMs },
        playback: { ...s.playback, endMs: durationMs },
      }));
      if (readTargetDurationMsForVisualizer(visualizer, 0) <= 0) {
        setTargetDurationMsForVisualizer(visualizer, durationMs);
      }
      renderCursor(visualizer, readFieldState(ord).cursor.ms, durationMs);
    },
    onErrorDuringPlayback(cursorMs) {
      const ord = fieldOrd(visualizer);
      const session = readHtmlAudioSessionState(ord);
      if (!htmlAudioErrorBelongsToActiveSession(session) && !fieldPlaybackUsesAudioClock(ord)) return;
      logger.warn("audio clock failed during playback", { ord });
      dispatchHtmlAudioSessionEvent(ord, {
        cursorMs: cursorMs || htmlAudioErrorCursorMs(ord, session),
        reason: "audio_error",
        type: "AudioError",
      });
      stopLegacyAudioPlaybackAfterEmptySessionError(visualizer, ord, cursorMs);
    },
    onEndedDuringPlayback(durationMs) {
      const ord = fieldOrd(visualizer);
      const session = readHtmlAudioSessionState(ord);
      if (session.kind !== "empty" && session.kind !== "failed" && session.source.kind === "source") {
        if (
          (session.kind === "starting" || session.kind === "playing") &&
          handleSelectedRepeatAutoAdvanceBoundary(visualizer, playbackPassForSessionRequest(session.request))
        ) {
          return;
        }
        dispatchSourceSessionBoundary(visualizer, ord, durationMs, session.kind === "ready");
        repaintCompletedSourceBoundaryCursor(visualizer, ord);
        return;
      }
      if (fieldPlaybackEngineIsHtml(ord)) {
        dispatchSourceSessionBoundary(visualizer, ord, durationMs, true);
        repaintCompletedSourceBoundaryCursor(visualizer, ord);
        return;
      }
      if (session.kind !== "starting" && session.kind !== "playing") {
        handleLegacyAudioPlaybackEnded(visualizer, durationMs);
        return;
      }
      handleLegacyAudioPlaybackEnded(visualizer, durationMs);
    },
  });
}

function handleHtmlAudioSourceBoundary(
  visualizer: VisualizerElement,
  request: HtmlAudioStartRequest,
): boolean {
  return handleSelectedRepeatAutoAdvanceBoundary(
    visualizer,
    playbackPassForSessionRequest(request),
  ) !== false;
}

function fieldPlaybackEngineIsHtml(ord: number): boolean {
  return readFieldState(ord).playback.engine === "html";
}

function htmlAudioErrorBelongsToActiveSession(session: ReturnType<typeof readHtmlAudioSessionState>): boolean {
  if (session.kind === "loading") return session.pendingStart !== null;
  return session.kind === "starting" || session.kind === "playing";
}

function htmlAudioErrorCursorMs(ord: number, session: ReturnType<typeof readHtmlAudioSessionState>): number {
  if ("request" in session) return session.request.cursorMs;
  return readFieldState(ord).cursor.ms;
}

function dispatchSourceSessionBoundary(
  visualizer: VisualizerElement,
  ord: number,
  durationMs: number,
  includeRequest: boolean,
): void {
  const request = sourceBoundaryRequest(visualizer, ord, durationMs);
  const event = {
    cursorMs: durationMs,
    repeatEnabled: repeatEnabledFor(visualizer),
    repeatPauseMs: readRepeatPauseSecondsRuntime(visualizer) * 1000,
    resetCursorMs: request.resetCursorMs ?? request.cursorMs,
    restartAudio: true,
    type: "BoundaryReached",
  } as const;
  dispatchHtmlAudioSessionEvent(ord, includeRequest ? { ...event, request } : event);
}

function sourceBoundaryRequest(
  visualizer: VisualizerElement,
  ord: number,
  durationMs: number,
): HtmlAudioStartRequest {
  const field = readFieldState(ord);
  const regionMode = field.playback.regionMode === "selection" ? "selection" : "full";
  const cursorMs = Math.round(field.playback.startMs || 0);
  return {
    cursorMs,
    endMs: Math.round(field.playback.endMs || field.graph.durationMs || durationMs),
    loop: repeatEnabledFor(visualizer),
    ord,
    regionMode,
    resetCursorMs: regionMode === "selection" && field.selection.startMs !== null
      ? Math.round(field.selection.startMs)
      : Math.round(field.cursor.anchorMs),
    source: preserveStatusOnPlaybackEndRuntime(visualizer) ? "post_edit" : "user",
  };
}

function stopLegacyAudioPlaybackAfterEmptySessionError(
  visualizer: VisualizerElement,
  ord: number,
  cursorMs: number,
): void {
  if (readHtmlAudioSessionState(ord).kind !== "empty") return;
  stopProgressClock(visualizer, { clearEngine: false });
  updateFieldState(ord, (field) => ({
    ...field,
    cursor: {
      ...field.cursor,
      ms: cursorMs,
      progressMs: cursorMs,
    },
  }));
}

function handleLegacyAudioPlaybackEnded(visualizer: VisualizerElement, durationMs: number): void {
  if (repeatEnabledFor(visualizer)) {
    const field = readFieldState(fieldOrd(visualizer));
    if (field.graph.durationMs <= 0 && durationMs > 0) {
      updateFieldState(field.ord, (state) => ({
        ...state,
        graph: { ...state.graph, durationMs },
        playback: { ...state.playback, endMs: durationMs },
      }));
      setTargetDurationMsForVisualizer(visualizer, durationMs);
    }
    startProgressClock(visualizer, field.playback.startMs || 0, {
      allowLoadingAudio: true,
      engine: "html",
      manualFallback: false,
    });
    return;
  }
  completePlayback(visualizer);
  const field = readFieldState(fieldOrd(visualizer));
  renderCursor(visualizer, field.cursor.ms, field.graph.durationMs);
}

function repaintCompletedSourceBoundaryCursor(visualizer: VisualizerElement, ord: number): void {
  const field = readFieldState(ord);
  if (field.playback.state !== "stopped") return;
  ensurePlaybackCursorVisible(visualizer, field.cursor.ms);
  renderCursor(visualizer, field.cursor.ms, field.graph.durationMs);
}

function playbackPassForSessionRequest(request: {
  cursorMs: number;
  endMs: number;
  loop: boolean;
  regionMode: "full" | "selection";
  resetCursorMs?: number;
}): PlaybackPass {
  return {
    endMs: request.endMs,
    loop: request.loop,
    regionMode: request.regionMode,
    resetCursorMs: request.resetCursorMs ?? request.cursorMs,
    startMs: request.cursorMs,
  };
}

export function audioClockReady(visualizer: VisualizerElement | null): boolean {
  return isAudioClockReady(visualizer);
}

export function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = readFieldState(fieldOrd(visualizer)).graph.durationMs;
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}

export function setRepeatEnabled(visualizer: VisualizerElement, enabled: boolean): void {
  projectRepeatEnabled(visualizer, enabled);
  if (!enabled && isRepeatPauseWaitingRuntime(visualizer)) {
    completePlayback(visualizer);
  }
}
export { repeatEnabledFor };
