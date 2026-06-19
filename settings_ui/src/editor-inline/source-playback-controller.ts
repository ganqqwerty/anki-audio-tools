import { setStatus } from "./control-actions.js";
import { readFieldState, updateFieldState } from "./field-state-store.js";
import { logger } from "./logger.js";
import type { PlaybackEngineDecision } from "./playback-engine-decision.js";
import type { ProgressClockOptions } from "./playback-controller.js";
import type { PlaybackPass } from "./playback-model.js";
import { clearRepeatPauseTimer } from "./playback-controller-frame.js";
import { playbackTelemetryContext } from "./playback-telemetry.js";
import {
  restartLoopPlaybackNow,
  scheduleRepeatLoopPlayback,
} from "./source-playback-repeat-loop.js";
import {
  transitionSourcePlayback,
  type SourcePlaybackEffect,
  type SourcePlaybackEvent,
  type SourcePlaybackRequest,
  type SourcePlaybackState,
  type SourcePlaybackTransition,
} from "./source-playback-machine.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";
import { t } from "../lib/i18n.js";
import {
  preserveStatusOnPlaybackEndRuntime,
  readRepeatPauseSecondsRuntime,
  readTargetDurationMsForVisualizer,
} from "./visualizer-runtime-state.js";

export interface SourcePlaybackRuntime {
  completePlayback: (visualizer: VisualizerElement) => void;
  paintProgressFromClock: (visualizer: VisualizerElement) => void;
  repeatEnabledFor: (visualizer: VisualizerElement) => boolean;
  sendPlaybackRequest: (request: PlaybackRequest) => void;
  setPlaybackButtonLabel: (visualizer: VisualizerElement, label: string) => void;
  startManualProgressClock: (visualizer: VisualizerElement, startMs: number) => void;
  startProgressClock: (
    visualizer: VisualizerElement,
    startMs: number,
    options?: ProgressClockOptions,
  ) => void;
  stopProgressClock: (
    visualizer: VisualizerElement,
    options?: { clearAudio?: boolean; clearEngine?: boolean },
  ) => void;
}

export interface SourcePlaybackContext {
  decision: PlaybackEngineDecision;
  request: PlaybackRequest;
  runtime: SourcePlaybackRuntime;
  visualizer: VisualizerElement;
}

export interface SourcePlaybackExecutionOptions {
  forceAudioPlay?: boolean;
  repeatPass?: PlaybackPass;
  syncBackend?: boolean;
}

export function startSourceHtmlPlayback(
  visualizer: VisualizerElement,
  request: PlaybackRequest,
  runtime: SourcePlaybackRuntime,
): boolean {
  clearPostEditPlaybackWarning(visualizer);
  const sourceRequest = sourcePlaybackRequestFor(visualizer, request);
  const state = readySourcePlaybackState(visualizer, sourceRequest);
  const event = sourceRequest.source === "post_edit"
    ? { request: sourceRequest, type: "PostEditAutoplayRequested" as const }
    : { request: sourceRequest, type: "UserPlayRequested" as const };
  const transition = transitionSourcePlayback(state, event);
  executeSourcePlaybackTransition(transition, {
    decision: { engine: "html", reason: "audio_clock_ready" },
    request: { ...request, engine: "html" },
    runtime,
    visualizer,
  });
  return true;
}

export function dispatchSourcePlaybackEvent(
  visualizer: VisualizerElement,
  event: SourcePlaybackEvent,
  runtime: SourcePlaybackRuntime,
): void {
  const state = sourcePlaybackStateForEvent(visualizer, event);
  const transition = transitionSourcePlayback(state, event);
  const sourceRequest = sourceRequestForState(visualizer, state, event);
  executeSourcePlaybackTransition(transition, {
    decision: { engine: "html", reason: "audio_clock_ready" },
    request: playbackRequestForSourceRequest(sourceRequest),
    runtime,
    visualizer,
  });
}

export function handleSourcePlaybackBoundary(
  visualizer: VisualizerElement,
  pass: PlaybackPass,
  repeatPauseMs: number,
  runtime: SourcePlaybackRuntime,
  options: { forceAudioPlay?: boolean } = {},
): boolean {
  if (!pass.loop) {
    runtime.completePlayback(visualizer);
    return true;
  }
  const state = sourcePlaybackStateForPass(visualizer, pass, repeatPauseMs);
  const transition = transitionSourcePlayback(state, {
    cursorMs: pass.endMs,
    type: "BoundaryReached",
  });
  executeSourcePlaybackTransition(transition, {
    decision: { engine: "html", reason: "audio_clock_ready" },
    request: playbackRequestForSourceRequest(state.request),
    runtime,
    visualizer,
  }, { ...options, repeatPass: pass });
  return true;
}

function executeSourcePlaybackTransition(
  transition: SourcePlaybackTransition,
  context: SourcePlaybackContext,
  options: SourcePlaybackExecutionOptions = {},
): void {
  for (const effect of transition.effects) {
    executeSourcePlaybackEffect(effect, transition.state, context, options);
  }
}

function executeSourcePlaybackEffect(
  effect: SourcePlaybackEffect,
  state: SourcePlaybackState,
  context: SourcePlaybackContext,
  options: SourcePlaybackExecutionOptions,
): void {
  switch (effect.type) {
    case "SeekAudio":
      return;
    case "PlayAudio":
      if (options.repeatPass) {
        restartLoopPlaybackNow(context, options, options.repeatPass);
      } else {
        startHtmlAudio(effect, state, context);
      }
      return;
    case "PauseAudio":
    case "StopAudio":
      context.runtime.stopProgressClock(
        context.visualizer,
        state.kind === "repeat_waiting" ? { clearEngine: false } : {},
      );
      syncFailedCursor(context.visualizer, state);
      return;
    case "PublishPlaybackState":
      if (options.syncBackend) {
        context.runtime.sendPlaybackRequest({ ...context.request, engine: "html" });
      }
      return;
    case "ShowPlaybackStatus":
      if (context.request.source === "post_edit") {
        showPostEditPlaybackWarning(context.visualizer, t(effect.statusKey), effect.kind);
        return;
      }
      setStatus(t(effect.statusKey), effect.kind ?? "warning", "playback");
      return;
    case "LogPlaybackTelemetry":
      logger.debug(effect.event, playbackTelemetryContext(
        context.visualizer,
        context.decision,
        effect.data,
      ));
      return;
    case "ClearRepeatTimer":
      clearRepeatPauseTimer(context.visualizer);
      return;
    case "ClearMetadataTimer":
      return;
    case "ConfigureAudioSource":
    case "ProbeAudioMetadata":
    case "StartMetadataTimer":
      return;
    case "StartRepeatTimer":
      scheduleRepeatLoopPlayback(effect, state, context, options, executeSourcePlaybackTransition);
      return;
    default:
      return exhaustive(effect);
  }
}

function startHtmlAudio(
  _effect: Extract<SourcePlaybackEffect, { type: "PlayAudio" }>,
  state: SourcePlaybackState,
  context: SourcePlaybackContext,
): void {
  if (state.kind !== "starting") return;
  context.runtime.startProgressClock(context.visualizer, state.request.cursorMs, {
    allowLoadingAudio: state.request.source === "post_edit" && Math.round(state.request.cursorMs) <= 0,
    engine: "html",
    manualFallback: false,
    onAudioStarted() {
      const resolved = transitionSourcePlayback(state, { type: "PlayResolved" });
      executeSourcePlaybackTransition(resolved, context, { syncBackend: true });
    },
    onAudioPlayFailed(reason = "audio_play_rejected") {
      const event = reason === "audio_seek_failed"
        ? { cursorMs: state.request.cursorMs, reason, type: "SeekFailed" as const }
        : { cursorMs: state.request.cursorMs, reason, type: "PlayRejected" as const };
      const rejected = transitionSourcePlayback(state, event);
      executeSourcePlaybackTransition(rejected, context);
    },
  });
}

function sourcePlaybackRequestFor(
  visualizer: VisualizerElement,
  request: PlaybackRequest,
): SourcePlaybackRequest {
  return {
    cursorMs: request.cursorMs,
    endMs: request.endMs ?? readTargetDurationMsForVisualizer(visualizer, 0),
    loop: request.loop === true,
    ord: request.ord,
    regionMode: request.regionMode ?? "full",
    repeatPauseMs: readRepeatPauseSecondsRuntime(visualizer) * 1000,
    source: request.source ?? "user",
  };
}

function sourcePlaybackStateForEvent(
  visualizer: VisualizerElement,
  event: SourcePlaybackEvent,
): SourcePlaybackState {
  const sourceRequest = sourceRequestForState(visualizer, null, event);
  const state = readFieldState(sourceRequest.ord);
  const durationMs = state.graph.durationMs || sourceRequest.endMs;
  const sourceFilename = state.sourceFilename;
  if (!sourceFilename) {
    return {
      cursorMs: sourceRequest.cursorMs,
      kind: "unconfigured",
      reason: "audio_src_missing",
    };
  }
  if (state.playback.state === "playing") {
    return {
      durationMs,
      kind: "playing",
      request: sourceRequest,
      sourceFilename,
    };
  }
  if (state.playback.state === "paused") {
    return {
      durationMs,
      kind: "paused",
      pausedAtMs: sourceRequest.cursorMs,
      request: sourceRequest,
      sourceFilename,
    };
  }
  return {
    cursorMs: sourceRequest.cursorMs,
    durationMs,
    kind: "ready",
    sourceFilename,
  };
}

function sourcePlaybackStateForPass(
  visualizer: VisualizerElement,
  pass: PlaybackPass,
  repeatPauseMs: number,
): Extract<SourcePlaybackState, { kind: "playing" }> {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const state = readFieldState(ord);
  const request: SourcePlaybackRequest = {
    cursorMs: pass.startMs,
    endMs: pass.endMs,
    loop: pass.loop,
    ord,
    regionMode: pass.regionMode,
    repeatPauseMs,
    source: preserveStatusOnPlaybackEndRuntime(visualizer) ? "post_edit" : "user",
  };
  return {
    durationMs: state.graph.durationMs || pass.endMs,
    kind: "playing",
    request,
    sourceFilename: state.sourceFilename,
  };
}

function sourceRequestForState(
  visualizer: VisualizerElement,
  state: SourcePlaybackState | null,
  event: SourcePlaybackEvent,
): SourcePlaybackRequest {
  if ("request" in event) return event.request;
  if (state && "request" in state) return state.request;
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const field = readFieldState(ord);
  const cursorMs = "cursorMs" in event ? event.cursorMs : field.cursor.ms;
  const endMs = field.playback.endMs || readTargetDurationMsForVisualizer(visualizer, 0);
  return {
    cursorMs,
    endMs,
    loop: field.playback.repeat,
    ord,
    regionMode: field.playback.regionMode,
    repeatPauseMs: readRepeatPauseSecondsRuntime(visualizer) * 1000,
    source: preserveStatusOnPlaybackEndRuntime(visualizer) ? "post_edit" : "user",
  };
}

function playbackRequestForSourceRequest(request: SourcePlaybackRequest): PlaybackRequest {
  return {
    action: "start",
    cursorMs: request.cursorMs,
    endMs: request.endMs,
    engine: "html",
    loop: request.loop,
    ord: request.ord,
    regionMode: request.regionMode,
    source: request.source,
  };
}

function readySourcePlaybackState(
  visualizer: VisualizerElement,
  request: SourcePlaybackRequest,
): SourcePlaybackState {
  const state = readFieldState(request.ord);
  return {
    cursorMs: request.cursorMs,
    durationMs: state.graph.durationMs || request.endMs,
    kind: "ready",
    sourceFilename: state.sourceFilename,
  };
}

function showPostEditPlaybackWarning(
  visualizer: VisualizerElement,
  message: string,
  kind: "info" | "warning" | "error" = "warning",
): void {
  if (kind === "info") return;
  const warning = playbackWarningForVisualizer(visualizer);
  if (!warning) return;
  warning.textContent = message;
  warning.dataset.kind = kind;
  warning.hidden = false;
}

function clearPostEditPlaybackWarning(visualizer: VisualizerElement): void {
  const warning = playbackWarningForVisualizer(visualizer);
  if (!warning) return;
  warning.textContent = "";
  delete warning.dataset.kind;
  warning.hidden = true;
}

function syncFailedCursor(visualizer: VisualizerElement, state: SourcePlaybackState): void {
  if (state.kind !== "failed") return;
  const cursorMs = Math.round(Number.isFinite(state.cursorMs) ? state.cursorMs : 0);
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  updateFieldState(ord, (field) => ({
    ...field,
    cursor: {
      ...field.cursor,
      ms: cursorMs,
      progressMs: cursorMs,
    },
  }));
}

function playbackWarningForVisualizer(visualizer: VisualizerElement): HTMLElement | null {
  return visualizer
    .closest<HTMLElement>(".aqe-controls")
    ?.querySelector<HTMLElement>(".aqe-playback-warning") ?? null;
}

function exhaustive(value: never): never {
  throw new Error(`Unhandled source playback effect: ${JSON.stringify(value)}`);
}
