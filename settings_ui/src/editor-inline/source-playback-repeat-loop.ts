import {
  audioClockFor,
  audioClockReady,
  pauseAudioClock,
  reloadAudioClockSource,
  seekAudioClock,
  setAudioClockLoop,
} from "./audio-clock.js";
import { markHtmlAudioFailure } from "./audio-readiness.js";
import { readFieldState, writeFieldState } from "./field-state-store.js";
import { startRepeatPauseCountdownOverlay } from "./graph-countdown-overlay.js";
import {
  clearPlaybackFrame,
  clearRepeatPauseTimer,
} from "./playback-controller-frame.js";
import { writePlaybackPass } from "./playback-controller-pass.js";
import { startPlaybackPlan } from "./playback-plan-state.js";
import type { PlaybackPass } from "./playback-model.js";
import {
  transitionSourcePlayback,
  type SourcePlaybackEffect,
  type SourcePlaybackState,
  type SourcePlaybackTransition,
} from "./source-playback-machine.js";
import type {
  SourcePlaybackContext,
  SourcePlaybackExecutionOptions,
} from "./source-playback-controller.js";
import type { VisualizerElement } from "./types.js";
import { renderCursor } from "./visualizer-renderer.js";
import {
  setPlaybackClockRuntime,
  setRepeatPauseWaitingRuntime,
} from "./visualizer-runtime-state.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";

export type SourcePlaybackTransitionExecutor = (
  transition: SourcePlaybackTransition,
  context: SourcePlaybackContext,
  options?: SourcePlaybackExecutionOptions,
) => void;

export function scheduleRepeatLoopPlayback(
  effect: Extract<SourcePlaybackEffect, { type: "StartRepeatTimer" }>,
  state: SourcePlaybackState,
  context: SourcePlaybackContext,
  options: SourcePlaybackExecutionOptions,
  executeTransition: SourcePlaybackTransitionExecutor,
): void {
  if (state.kind !== "repeat_waiting" || !options.repeatPass) return;
  const visualizer = context.visualizer;
  const loopStartMs = options.repeatPass.startMs;
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  writePlaybackPass(visualizer, options.repeatPass);
  setPlaybackClockRuntime(visualizer, loopStartMs);
  const field = readFieldState(context.request.ord);
  writeFieldState(context.request.ord, {
    ...field,
    playback: { ...field.playback, state: "playing", clockMode: "stopped" },
  });
  setRepeatPauseWaitingRuntime(visualizer, true);
  setLoopCursor(visualizer, context.request.ord, loopStartMs);
  ensurePlaybackCursorVisible(visualizer, loopStartMs);
  context.runtime.setPlaybackButtonLabel(visualizer, "Pause");
  startRepeatPauseCountdownOverlay(visualizer, effect.pauseMs);
  visualizer.__aqeRepeatPauseTimer = window.setTimeout(() => {
    visualizer.__aqeRepeatPauseTimer = null;
    clearRepeatPauseTimer(visualizer);
    if (readFieldState(context.request.ord).playback.state !== "playing") return;
    if (!context.runtime.repeatEnabledFor(visualizer)) {
      context.runtime.completePlayback(visualizer);
      return;
    }
    const elapsed = transitionSourcePlayback(state, { type: "RepeatDelayElapsed" });
    executeTransition(elapsed, context, {
      ...options,
      forceAudioPlay: true,
    });
  }, effect.pauseMs);
}

export function restartLoopPlaybackNow(
  context: SourcePlaybackContext,
  options: SourcePlaybackExecutionOptions,
  pass: PlaybackPass,
): void {
  const visualizer = context.visualizer;
  const loopStartMs = pass.startMs;
  clearRepeatPauseTimer(visualizer);
  writePlaybackPass(visualizer, pass);
  setPlaybackClockRuntime(visualizer, loopStartMs);
  const field = readFieldState(context.request.ord);
  writeFieldState(context.request.ord, {
    ...field,
    playback: { ...field.playback, state: "playing" },
  });
  setLoopCursor(visualizer, context.request.ord, loopStartMs);
  ensurePlaybackCursorVisible(visualizer, loopStartMs);
  const canUseAudioClock = audioClockReady(visualizer)
    && (field.playback.clockMode === "audio" || field.playback.engine === "html");
  if (field.playback.clockMode !== "audio" || !audioClockReady(visualizer)) {
    if (!canUseAudioClock) {
      context.runtime.startManualProgressClock(visualizer, loopStartMs);
      return;
    }
    const fresh = readFieldState(context.request.ord);
    writeFieldState(context.request.ord, {
      ...fresh,
      playback: { ...fresh.playback, clockMode: "audio" },
    });
  }
  setAudioClockLoop(visualizer, false);
  if (fullSourcePass(pass, field.graph.durationMs) && loopStartMs <= 0) {
    restartFullSourceAudioLoop(context, pass);
    return;
  }
  if (!seekAudioClock(visualizer, loopStartMs, field.graph.durationMs)) {
    context.runtime.startManualProgressClock(visualizer, loopStartMs);
    return;
  }
  if (!options.forceAudioPlay && readFieldState(context.request.ord).playback.clockMode === "audio") {
    clearPlaybackFrame(visualizer);
    startPlaybackPlan(visualizer, loopStartMs, pass.endMs);
    context.runtime.paintProgressFromClock(visualizer);
    return;
  }
  const audio = audioClockFor(visualizer);
  if (!audio || typeof audio.play !== "function") return;
  setAudioClockLoop(visualizer, false);
  clearPlaybackFrame(visualizer);
  const playGeneration = visualizer.__aqePlaybackGeneration ?? 0;
  void Promise.resolve(audio.play())
    .then(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      const latest = readFieldState(context.request.ord);
      if (latest.playback.state === "playing") {
        writeFieldState(context.request.ord, {
          ...latest,
          playback: { ...latest.playback, clockMode: "audio" },
        });
        startPlaybackPlan(visualizer, loopStartMs, pass.endMs);
        context.runtime.paintProgressFromClock(visualizer);
      }
    })
    .catch(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      if (readFieldState(context.request.ord).playback.state === "playing") {
        markHtmlAudioFailure(visualizer, "audio_play_rejected");
        context.runtime.startManualProgressClock(visualizer, loopStartMs);
      }
    });
}

function restartFullSourceAudioLoop(
  context: SourcePlaybackContext,
  pass: PlaybackPass,
): void {
  const visualizer = context.visualizer;
  const audio = audioClockFor(visualizer);
  if (!audio || typeof audio.play !== "function") {
    context.runtime.startManualProgressClock(visualizer, pass.startMs);
    return;
  }
  if (!reloadAudioClockSource(visualizer)) {
    context.runtime.startManualProgressClock(visualizer, pass.startMs);
    return;
  }
  clearPlaybackFrame(visualizer);
  const playGeneration = visualizer.__aqePlaybackGeneration ?? 0;
  void Promise.resolve(audio.play())
    .then(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      const field = readFieldState(context.request.ord);
      if (field.playback.state !== "playing") return;
      writeFieldState(context.request.ord, {
        ...field,
        playback: { ...field.playback, clockMode: "audio" },
      });
      startPlaybackPlan(visualizer, pass.startMs, pass.endMs);
      context.runtime.paintProgressFromClock(visualizer);
    })
    .catch(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      if (readFieldState(context.request.ord).playback.state === "playing") {
        markHtmlAudioFailure(visualizer, "audio_play_rejected");
        context.runtime.startManualProgressClock(visualizer, pass.startMs);
      }
    });
}

function fullSourcePass(pass: PlaybackPass, durationMs: number): boolean {
  return durationMs > 0
    && pass.resetCursorMs <= 0
    && pass.endMs >= Math.max(0, durationMs - 20);
}

function setLoopCursor(visualizer: VisualizerElement, ord: number, ms: number): void {
  const field = readFieldState(ord);
  const cursorMs = Math.round(ms);
  writeFieldState(ord, {
    ...field,
    cursor: {
      ...field.cursor,
      ms: cursorMs,
      progressMs: cursorMs,
    },
  });
  renderCursor(visualizer, cursorMs, field.graph.durationMs);
}
