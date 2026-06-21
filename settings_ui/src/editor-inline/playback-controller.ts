import {
  audioClockFor,
  audioClockReady,
  seekAudioElementForCursorPreview,
} from "./audio-clock.js";
import {
  dispatchHtmlAudioSessionEvent,
  readHtmlAudioSessionState,
} from "./html-audio-session-controller.js";
import { markHtmlAudioFailure } from "./audio-readiness.js";
import { logger } from "./logger.js";
import {
  clearRepeatPauseCountdownOverlay,
  startRepeatPauseCountdownOverlay,
} from "./graph-countdown-overlay.js";
import {
  clampProgressMs,
  liveProgressMs,
  repeatPauseDelayMs,
  startPlaybackPlan,
} from "./playback-plan-state.js";
import {
  planPlaybackBoundary,
  playbackStateIsStopped,
  type PlaybackPass,
  type PlaybackRegion,
} from "./playback-model.js";
import {
  activePlaybackPass,
  playbackEndMs,
  plannedPlaybackPass,
  setPlaybackPass,
  writePlaybackPass,
} from "./playback-controller-pass.js";
import {
  clearPlaybackFrame,
} from "./playback-controller-frame.js";
import { completePlayback, stopProgressClock } from "./playback-controller-state.js";
import type { PlaybackState, VisualizerElement } from "./types.js";
import {
  renderPlaybackCursor,
} from "./visualizer-renderer.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
import { readFieldState, writeFieldState } from "./field-state-store.js";
import type { EditorFieldState } from "./field-state.js";
import {
  setPlaybackClockRuntime,
  setRepeatPauseWaitingRuntime,
} from "./visualizer-runtime-state.js";

export { clearPlaybackFrame };
export {
  audioProgressMs,
  currentProgressMs,
  manualProgressMs,
} from "./playback-controller-audio.js";
export {
  completePlayback,
  pauseProgressClock,
  stopProgressClock,
} from "./playback-controller-state.js";

const HTML_FULL_SOURCE_REPEAT_PREEMPT_MS = 40;

function fieldState(visualizer: VisualizerElement): EditorFieldState {
  return readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function playbackStopped(visualizer: VisualizerElement): boolean {
  return playbackStateIsStopped(fieldState(visualizer).playback.state);
}

function stopSessionAudioForManualClock(visualizer: VisualizerElement, cursorMs: number): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const session = readHtmlAudioSessionState(ord);
  const activeSession = session.kind === "starting" || session.kind === "playing" || session.kind === "paused" || session.kind === "repeat_waiting";
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs,
    type: activeSession ? "StopRequested" : "PauseRequested",
  });
}

export interface ProgressClockOptions {
  allowLoadingAudio?: boolean;
  engine?: "html" | "";
  manualFallback?: boolean;
  onAudioPlayFailed?: (reason?: "audio_play_rejected" | "audio_seek_failed") => void;
  onAudioStarted?: () => void;
}

export interface PlaybackControllerDependencies {
  clearStatus: (ord: number) => void;
  effectivePlaybackRegion: (visualizer: VisualizerElement) => PlaybackRegion;
  focusAndSendCommand: (ord: number, command: string) => void;
  handleLoopBoundary?: (visualizer: VisualizerElement, pass: PlaybackPass) => boolean;
  playbackEngineFor: (visualizer: VisualizerElement | null) => "html";
  repeatEnabledFor: (visualizer: VisualizerElement) => boolean;
  restoreStatus: (ord: number) => void;
  setCursor: (
    visualizer: VisualizerElement,
    ms: number,
    notifyPython: boolean,
    options?: {
      engine?: "html" | "";
      previousPlaybackState?: PlaybackState;
      restartPlayback?: boolean;
      updateAnchor?: boolean;
    },
  ) => void;
  setPlaybackButtonLabel: (visualizer: VisualizerElement, label: string) => void;
  stopOtherPlayback: (activeVisualizer: VisualizerElement) => void;
}

export function handlePlaybackBoundary(
  visualizer: VisualizerElement,
  nextMs: number,
  deps: PlaybackControllerDependencies,
): boolean {
  const boundary = planPlaybackBoundary({
    nextMs,
    pass: activePlaybackPass(visualizer, deps),
    repeat: deps.repeatEnabledFor(visualizer),
    repeatPauseMs: repeatPauseDelayMs(visualizer),
  });
  if (boundary.kind === "continue") return false;
  if (boundary.kind === "loop") {
    if (deps.handleLoopBoundary?.(visualizer, boundary.pass) === true) {
      return true;
    }
    if (boundary.repeatPauseMs > 0) {
      startManualRepeatPause(visualizer, boundary.pass, deps, boundary.repeatPauseMs);
      return true;
    }
    startManualPlaybackPass(visualizer, boundary.pass, deps, boundary.pass.startMs);
    return true;
  }
  completePlayback(visualizer, deps);
  return true;
}

export function paintProgressFromClock(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): void {
  const generation = visualizer.__aqePlaybackGeneration ?? 0;
  const tick = (frameNowMs: number): void => {
    if (visualizer.__aqePlaybackGeneration !== generation) return;
    const s = fieldState(visualizer);
    if (s.playback.state !== "playing") return;
    const nextMs = liveProgressMs(visualizer, frameNowMs);
    if (nextMs === null) {
      startManualProgressClock(visualizer, s.cursor.ms, deps);
      return;
    }
    const pass = activePlaybackPass(visualizer, deps);
    const boundaryMs = htmlFullSourceRepeatBoundaryMs(
      nextMs,
      pass,
      s.graph.durationMs,
      s.playback.clockMode,
      deps.repeatEnabledFor(visualizer),
    );
    if (handlePlaybackBoundary(visualizer, boundaryMs, deps)) {
      return;
    }
    ensurePlaybackCursorVisible(visualizer, nextMs);
    renderPlaybackCursor(
      visualizer,
      nextMs,
      s.graph.durationMs,
      frameNowMs,
    );
    visualizer.__aqePlaybackTimer = window.requestAnimationFrame(tick);
  };
  visualizer.__aqePlaybackTimer = window.requestAnimationFrame(tick);
}

export function startManualProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  deps: PlaybackControllerDependencies,
): void {
  const s = fieldState(visualizer);
  const clampedStartMs = s.graph.durationMs ? clampProgressMs(visualizer, startMs) : Math.max(0, Number(startMs) || 0);
  const region = deps.effectivePlaybackRegion(visualizer);
  const passStartMs = region.mode === "selection" ? region.startMs : clampedStartMs;
  startManualPlaybackPass(visualizer, plannedPlaybackPass(visualizer, passStartMs, deps, region), deps, clampedStartMs);
}

function startManualPlaybackPass(
  visualizer: VisualizerElement,
  pass: PlaybackPass,
  deps: PlaybackControllerDependencies,
  clockStartMs: number = pass.startMs,
): void {
  clearPlaybackFrame(visualizer);
  stopSessionAudioForManualClock(visualizer, clockStartMs);
  const s = fieldState(visualizer);
  if (!s.graph.durationMs) return;
  visualizer.__aqeAudioClockFallback = true;
  writeFieldState(s.ord, {
    ...s,
    playback: { ...s.playback, state: "playing", clockMode: "manual" },
  });
  writePlaybackPass(visualizer, pass);
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  startPlaybackPlan(visualizer, clockStartMs, pass.endMs);
  paintProgressFromClock(visualizer, deps);
}

function startManualRepeatPause(
  visualizer: VisualizerElement,
  pass: PlaybackPass,
  deps: PlaybackControllerDependencies,
  pauseMs: number,
): void {
  clearPlaybackFrame(visualizer);
  stopSessionAudioForManualClock(visualizer, pass.startMs);
  const s = fieldState(visualizer);
  if (!s.graph.durationMs) return;
  writeFieldState(s.ord, {
    ...s,
    playback: { ...s.playback, state: "playing", clockMode: "stopped" },
  });
  writePlaybackPass(visualizer, pass);
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  deps.setCursor(visualizer, pass.startMs, false, { updateAnchor: false });
  ensurePlaybackCursorVisible(visualizer, pass.startMs);
  setRepeatPauseWaitingRuntime(visualizer, true);
  startRepeatPauseCountdownOverlay(visualizer, pauseMs);
  visualizer.__aqeRepeatPauseTimer = window.setTimeout(() => {
    visualizer.__aqeRepeatPauseTimer = null;
    clearRepeatPauseCountdownOverlay(visualizer);
    setRepeatPauseWaitingRuntime(visualizer, false);
    if (fieldState(visualizer).playback.state !== "playing") return;
    startManualPlaybackPass(visualizer, pass, deps, pass.startMs);
  }, Math.max(0, pauseMs));
}

export function startAudioProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  deps: PlaybackControllerDependencies,
  options: ProgressClockOptions = {},
): void {
  const audio = audioClockFor(visualizer);
  const s = fieldState(visualizer);
  if (!audio || typeof audio.play !== "function") {
    if (options.manualFallback === false) {
      options.onAudioPlayFailed?.();
      return;
    }
    startManualPlaybackPass(visualizer, activePlaybackPass(visualizer, deps), deps);
    return;
  }
  const canSeekImmediately = audioClockReady(visualizer);
  const canStartWithoutMetadata = options.allowLoadingAudio === true && Math.round(startMs) <= 0;
  if (canSeekImmediately) {
    if (!seekAudioElementForCursorPreview(visualizer, startMs, s.graph.durationMs)) {
      if (options.manualFallback === false) {
        options.onAudioPlayFailed?.("audio_seek_failed");
        return;
      }
      startManualPlaybackPass(visualizer, activePlaybackPass(visualizer, deps), deps);
      return;
    }
  } else if (canStartWithoutMetadata) {
    visualizer.__aqeAudioClockLastSeekedMs = 0;
  } else {
    if (options.manualFallback === false) {
      options.onAudioPlayFailed?.("audio_seek_failed");
      return;
    }
    startManualPlaybackPass(visualizer, activePlaybackPass(visualizer, deps), deps);
    return;
  }
  writeFieldState(s.ord, {
    ...s,
    playback: { ...s.playback, clockMode: "audio" },
  });
  visualizer.__aqeAudioClockFallback = false;
  const playGeneration = visualizer.__aqePlaybackGeneration ?? 0;
  const handlePlaybackFailure = (): void => {
    if (options.manualFallback === false) {
      options.onAudioPlayFailed?.();
      return;
    }
    startManualPlaybackPass(visualizer, activePlaybackPass(visualizer, deps), deps);
  };
  const startPainting = (): void => {
    if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
    const s2 = fieldState(visualizer);
    if (s2.playback.state !== "playing") return;
    clearPlaybackFrame(visualizer);
    writeFieldState(s2.ord, {
      ...s2,
      playback: { ...s2.playback, clockMode: "audio" },
    });
    startPlaybackPlan(visualizer, startMs, playbackEndMs(visualizer, deps));
    logger.info("html audio playback started", { ord: visualizer.dataset.aqeFieldOrd });
    paintProgressFromClock(visualizer, deps);
    options.onAudioStarted?.();
  };
  void Promise.resolve(audio.play())
    .then(startPainting)
    .catch(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      if (fieldState(visualizer).playback.state !== "playing") return;
      logger.warn("html audio play rejected; using manual clock", { ord: visualizer.dataset.aqeFieldOrd });
      markHtmlAudioFailure(visualizer, "audio_play_rejected");
      handlePlaybackFailure();
    });
}

export function startProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  deps: PlaybackControllerDependencies,
  options: ProgressClockOptions = {},
): void {
  const s = fieldState(visualizer);
  const selectedEngine = options.engine || s.playback.engine || "";
  stopProgressClock(visualizer, deps, { clearEngine: false });
  deps.stopOtherPlayback(visualizer);
  const clampedStartMs = s.graph.durationMs ? clampProgressMs(visualizer, startMs) : Math.max(0, Number(startMs) || 0);
  const fresh = readFieldState(s.ord);
  writeFieldState(s.ord, {
    ...fresh,
    playback: { ...fresh.playback, engine: selectedEngine, state: "playing" },
  });
  setPlaybackClockRuntime(visualizer, clampedStartMs);
  const pass = setPlaybackPass(visualizer, clampedStartMs, deps);
  if (s.graph.durationMs) {
    deps.setCursor(visualizer, clampedStartMs, false, { updateAnchor: false });
    ensurePlaybackCursorVisible(visualizer, clampedStartMs);
  } else {
    const cur = readFieldState(s.ord);
    writeFieldState(s.ord, {
      ...cur,
      cursor: { ...cur.cursor, ms: Math.round(clampedStartMs), progressMs: Math.round(clampedStartMs) },
    });
  }
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  logger.info("playback clock selected", { engine: selectedEngine || "auto", startMs: clampedStartMs });
  if (!s.graph.durationMs) return;
  if (audioClockReady(visualizer) || options.allowLoadingAudio === true) {
    startAudioProgressClock(visualizer, clampedStartMs, deps, options);
    return;
  }
  if (options.manualFallback === false) {
    options.onAudioPlayFailed?.();
    return;
  }
  startManualPlaybackPass(visualizer, pass, deps);
}

function htmlFullSourceRepeatBoundaryMs(
  nextMs: number,
  pass: PlaybackPass,
  durationMs: number,
  clockMode: string,
  repeat: boolean,
): number {
  if (
    clockMode === "audio"
    && repeat
    && fullSourcePass(pass, durationMs)
    && nextMs >= pass.endMs - HTML_FULL_SOURCE_REPEAT_PREEMPT_MS
  ) {
    return pass.endMs;
  }
  return nextMs;
}

function fullSourcePass(pass: PlaybackPass, durationMs: number): boolean {
  return durationMs > 0
    && pass.resetCursorMs <= 0
    && pass.endMs >= Math.max(0, durationMs - 20);
}
