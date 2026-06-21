import { sendGraphAnalysisRequest } from "./bridge.js";
import { setStatusForOrd } from "./control-actions.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { readFieldState, setCachedProgressMs } from "./field-state-store.js";
import { queueBackendPlayback } from "./html-audio-session-backend-queue.js";
import { audioProgressMsForOrd, createHtmlAudioElementOperations } from "./html-audio-session-audio-element.js";
import {
  initialHtmlAudioSessionState,
  transitionHtmlAudioSession,
  type HtmlAudioSessionEffect,
  type HtmlAudioSessionEvent,
  type HtmlAudioSessionState,
  type HtmlAudioStartRequest,
} from "./html-audio-session-machine.js";
import {
  clearPostEditReadyDispatches,
  dispatchPostEditReady,
} from "./html-audio-session-post-edit-dispatch.js";
import { completePlayback, publishPlaybackState, publishRepeatWaitingState } from "./html-audio-session-field-projection.js";
import {
  htmlAudioProgressDecision,
  type HtmlAudioProgressClock,
} from "./html-audio-session-progress.js";
import {
  clearLearnerAudioHandler,
  renderLearnerPlaybackCursor,
} from "./html-audio-session-learner-projection.js";
import { logger } from "./logger.js";
import { t } from "../lib/i18n.js";
import {
  readRepeatPauseSecondsRuntime,
  setPlaybackClockRuntime,
  setPlaybackPassRuntime,
  setRepeatPauseWaitingRuntime,
} from "./visualizer-runtime-state.js";
import { clearRepeatPauseCountdownOverlay, startRepeatPauseCountdownOverlay } from "./graph-countdown-overlay.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
import { renderPlaybackCursor } from "./visualizer-renderer.js";
import type { PlaybackPass } from "./playback-model.js";

const sessionStates = new Map<number, HtmlAudioSessionState>();
const progressFrames = new Map<number, number | null>();
const progressClocks = new Map<number, HtmlAudioProgressClock>();
const metadataTimers = new Map<number, number>();
const repeatTimers = new Map<number, number>();
const audioElementOperations = createHtmlAudioElementOperations(
  readHtmlAudioSessionState,
  dispatchHtmlAudioSessionEvent,
);

export function readHtmlAudioSessionState(ord: number): HtmlAudioSessionState {
  return sessionStates.get(ord) ?? initialHtmlAudioSessionState(ord);
}

export function dispatchHtmlAudioSessionEvent(ord: number, event: HtmlAudioSessionEvent): void {
  const current = readHtmlAudioSessionState(ord);
  const transition = transitionHtmlAudioSession(current, event);
  sessionStates.set(ord, transition.state);
  const expectedState = transition.state;
  for (const effect of transition.effects) {
    executeHtmlAudioSessionEffect(ord, effect);
    if (readHtmlAudioSessionState(ord) !== expectedState) {
      break;
    }
  }
}

export function clearHtmlAudioSession(ord: number): void {
  audioElementOperations.pauseAudio(ord);
  audioElementOperations.clearAudioSource(ord);
  clearProgressFrame(ord);
  clearMetadataTimer(ord);
  clearRepeatTimer(ord);
  clearLearnerAudioHandler(ord);
  sessionStates.delete(ord);
}

export function clearAllHtmlAudioSessions(): void {
  for (const ord of new Set([
    ...sessionStates.keys(),
    ...progressFrames.keys(),
    ...metadataTimers.keys(),
    ...repeatTimers.keys(),
  ])) {
    clearHtmlAudioSession(ord);
  }
  clearPostEditReadyDispatches();
}

export function stopOtherHtmlAudioSessions(activeOrd: number): void {
  for (const [ord, state] of sessionStates) {
    if (ord === activeOrd || !htmlAudioSessionIsActive(state)) continue;
    dispatchHtmlAudioSessionEvent(ord, {
      cursorMs: readFieldState(ord).cursor.ms,
      type: "StopRequested",
    });
  }
}

function executeHtmlAudioSessionEffect(ord: number, effect: HtmlAudioSessionEffect): void {
  switch (effect.type) {
    case "ConfigureAudioSource":
      audioElementOperations.configureAudioSource(ord, effect.sourceFilename);
      return;
    case "SeekAudio":
      audioElementOperations.seekAudio(ord, effect.cursorMs);
      return;
    case "ReloadAudioSource":
      audioElementOperations.reloadAudioSource(ord);
      return;
    case "PlayAudio":
      audioElementOperations.playAudio(ord);
      return;
    case "PauseAudio":
      audioElementOperations.pauseAudio(ord);
      return;
    case "ClearAudioSource":
      audioElementOperations.clearAudioSource(ord);
      return;
    case "StartProgressFrame":
      startProgressFrame(ord, effect.cursorMs, effect.endMs);
      return;
    case "ClearProgressFrame":
      clearProgressFrame(ord);
      return;
    case "StartRepeatTimer":
      startRepeatTimer(ord, effect.pauseMs);
      return;
    case "ClearRepeatTimer":
      clearRepeatTimer(ord);
      return;
    case "StartMetadataTimer":
      startMetadataTimer(ord, effect.timeoutMs);
      return;
    case "ClearMetadataTimer":
      clearMetadataTimer(ord);
      return;
    case "RequestGraphForSource":
      sendGraphAnalysisRequest({
        ord: effect.ord,
        sourceFilename: effect.sourceFilename,
      });
      return;
    case "DispatchPostEditReady":
      dispatchPostEditReady({
        command: "aqe:post-edit-playback-ready",
        fieldOrd: effect.ord,
        generation: effect.generation,
        sourceFilename: effect.sourceFilename,
      });
      return;
    case "QueueBackendPlayback":
      queueBackendPlayback(effect.request);
      return;
    case "PublishPlaybackState":
      publishPlaybackState({
        cursorMs: effect.cursorMs,
        dispatchEvent: dispatchHtmlAudioSessionEvent,
        ord,
        readState: readHtmlAudioSessionState,
        request: requestForFieldUpdate(ord),
        session: readHtmlAudioSessionState(ord),
        status: effect.status,
      });
      return;
    case "PublishRepeatWaitingState":
      publishRepeatWaitingState(ord, effect.cursorMs, requestForFieldUpdate(ord));
      return;
    case "CompletePlayback":
      completePlayback(ord, effect.cursorMs);
      return;
    case "ShowPlaybackStatus":
      setStatusForOrd(ord, t(effect.statusKey), "warning", "", "playback");
      return;
    case "ShowPostEditPlaybackWarning":
      showPostEditPlaybackWarning(ord, t(effect.statusKey));
      return;
    case "LogPlaybackTelemetry":
      logger.debug(effect.event, { ...effect.data, ord });
      return;
    default:
      return exhaustive(effect);
  }
}

function showPostEditPlaybackWarning(ord: number, message: string): void {
  const warning = visualizerForOrd(ord)
    ?.closest<HTMLElement>(".aqe-controls")
    ?.querySelector<HTMLElement>(".aqe-playback-warning") ?? null;
  if (!warning) return;
  warning.textContent = message;
  warning.dataset.kind = "warning";
  warning.hidden = false;
}

function startProgressFrame(ord: number, cursorMs: number, endMs: number): void {
  clearProgressFrame(ord);
  const visualizer = visualizerForOrd(ord);
  const session = readHtmlAudioSessionState(ord);
  const request = "request" in session ? session.request : null;
  if (visualizer && request && "source" in session && session.source?.kind === "source") {
    setPlaybackClockRuntime(visualizer, cursorMs);
    setPlaybackPassRuntime(visualizer, playbackPassForRequest(request));
    ensurePlaybackCursorVisible(visualizer, cursorMs);
  }
  setCachedProgressMs(ord, cursorMs, visualizer);
  if (typeof window.requestAnimationFrame !== "function") {
    progressFrames.set(ord, null);
    return;
  }
  progressClocks.set(ord, { cursorMs, endMs, startedAtMs: performance.now() });
  const tick = (): void => {
    const nowMs = performance.now();
    const state = readHtmlAudioSessionState(ord);
    if (state.kind !== "starting" && state.kind !== "playing") {
      clearProgressFrame(ord);
      return;
    }
    const clock = progressClocks.get(ord);
    if (!clock) return;
    const field = state.source.kind === "source" ? readFieldState(ord) : null;
    const currentVisualizer = state.source.kind === "source" ? visualizerForOrd(ord) : null;
    const graphDurationMs = field?.graph.durationMs ?? state.durationMs;
    const decision = htmlAudioProgressDecision({
      audioProgressMs: audioProgressMsForOrd(ord),
      clock,
      graphDurationMs,
      nowMs,
      repeatEnabled: field?.playback.repeat ?? false,
      repeatPauseMs: currentVisualizer ? readRepeatPauseSecondsRuntime(currentVisualizer) * 1000 : 0,
      state,
    });
    if (decision.kind === "learner_progress") {
      renderLearnerPlaybackCursor(ord, decision.learnerCursorMs);
    } else {
      setCachedProgressMs(ord, decision.progressMs, currentVisualizer);
      if (currentVisualizer) {
        ensurePlaybackCursorVisible(currentVisualizer, decision.progressMs);
        renderPlaybackCursor(currentVisualizer, decision.progressMs, graphDurationMs, nowMs);
      }
      if (decision.kind === "boundary") {
        dispatchHtmlAudioSessionEvent(ord, decision.event);
        return;
      }
    }
    progressFrames.set(ord, window.requestAnimationFrame(tick));
  };
  progressFrames.set(ord, window.requestAnimationFrame(tick));
}

function playbackPassForRequest(request: HtmlAudioStartRequest): PlaybackPass {
  return {
    endMs: request.endMs,
    loop: request.loop,
    regionMode: request.regionMode,
    resetCursorMs: resetCursorMsForRequest(request),
    startMs: request.cursorMs,
  };
}

function resetCursorMsForRequest(request: HtmlAudioStartRequest): number {
  if (request.resetCursorMs !== undefined) return Math.round(request.resetCursorMs);
  if (request.regionMode === "selection") {
    const selectionStartMs = readFieldState(request.ord).selection.startMs;
    if (selectionStartMs !== null) return Math.round(selectionStartMs);
  }
  return request.cursorMs;
}

function clearProgressFrame(ord: number): void {
  const frame = progressFrames.get(ord);
  if (frame !== undefined && frame !== null && typeof window.cancelAnimationFrame === "function") {
    window.cancelAnimationFrame(frame);
  }
  progressFrames.delete(ord);
  progressClocks.delete(ord);
}

function startMetadataTimer(ord: number, timeoutMs: number): void {
  clearMetadataTimer(ord);
  metadataTimers.set(ord, window.setTimeout(() => {
    metadataTimers.delete(ord);
    dispatchHtmlAudioSessionEvent(ord, { type: "MetadataTimeout" });
  }, Math.max(0, timeoutMs)));
}

function clearMetadataTimer(ord: number): void {
  const timer = metadataTimers.get(ord);
  if (timer !== undefined) {
    window.clearTimeout(timer);
  }
  metadataTimers.delete(ord);
}

function startRepeatTimer(ord: number, pauseMs: number): void {
  clearRepeatTimer(ord);
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    setRepeatPauseWaitingRuntime(visualizer, true);
    startRepeatPauseCountdownOverlay(visualizer, pauseMs);
  }
  repeatTimers.set(ord, window.setTimeout(() => {
    repeatTimers.delete(ord);
    const currentVisualizer = visualizerForOrd(ord);
    if (currentVisualizer) {
      setRepeatPauseWaitingRuntime(currentVisualizer, false);
      clearRepeatPauseCountdownOverlay(currentVisualizer);
    }
    const field = readFieldState(ord);
    if (field.playback.state !== "playing") return;
    dispatchHtmlAudioSessionEvent(ord, {
      repeatEnabled: field.playback.repeat,
      type: "RepeatDelayElapsed",
    });
  }, Math.max(0, pauseMs)));
}

function clearRepeatTimer(ord: number): void {
  const timer = repeatTimers.get(ord);
  if (timer !== undefined) {
    window.clearTimeout(timer);
  }
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    setRepeatPauseWaitingRuntime(visualizer, false);
    clearRepeatPauseCountdownOverlay(visualizer);
  }
  repeatTimers.delete(ord);
}

function requestForFieldUpdate(ord: number): HtmlAudioStartRequest | null {
  const state = readHtmlAudioSessionState(ord);
  return "request" in state ? state.request : null;
}

function htmlAudioSessionIsActive(state: HtmlAudioSessionState): boolean {
  return state.kind === "starting" ||
    state.kind === "playing" ||
    state.kind === "paused" ||
    state.kind === "repeat_waiting";
}

function exhaustive(value: never): never {
  throw new Error(`Unhandled html audio session effect: ${JSON.stringify(value)}`);
}
