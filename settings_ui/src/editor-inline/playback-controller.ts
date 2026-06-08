import {
  audioClockFor,
  audioClockReady,
  clearAudioClockSource,
  pauseAudioClock,
  seekAudioClock,
} from "./audio-clock.js";
import { startRepeatPauseCountdownOverlay } from "./graph-countdown-overlay.js";
import { logger } from "./logger.js";
import {
  clampProgressMs,
  liveProgressMs,
  repeatPauseDelayMs,
  startPlaybackPlan,
} from "./playback-plan-state.js";
import {
  planPlaybackBoundary,
  playbackCompletionCursor,
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
  clearRepeatPauseTimer,
} from "./playback-controller-frame.js";
import type { PlaybackState, VisualizerElement } from "./types.js";
import {
  renderPlaybackCursor,
} from "./visualizer-renderer.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";

export { clearPlaybackFrame };

export interface ProgressClockOptions {
  engine?: "html" | "native" | "";
  manualFallback?: boolean;
  onAudioPlayFailed?: () => void;
  onAudioStarted?: () => void;
}

export interface PlaybackControllerDependencies {
  clearStatus: (ord: number) => void;
  effectivePlaybackRegion: (visualizer: VisualizerElement) => PlaybackRegion;
  focusAndSendCommand: (ord: number, command: string) => void;
  playbackEngineFor: (visualizer: VisualizerElement | null) => "html" | "native";
  repeatEnabledFor: (visualizer: VisualizerElement) => boolean;
  restoreStatus: (ord: number) => void;
  setCursor: (
    visualizer: VisualizerElement,
    ms: number,
    notifyPython: boolean,
    options?: {
      engine?: "html" | "native" | "";
      previousPlaybackState?: PlaybackState;
      restartPlayback?: boolean;
      updateAnchor?: boolean;
    },
  ) => void;
  setPlaybackButtonLabel: (visualizer: VisualizerElement, label: string) => void;
  stopOtherPlayback: (activeVisualizer: VisualizerElement) => void;
}

export function manualProgressMs(visualizer: VisualizerElement): number {
  const planned = liveProgressMs(visualizer);
  if (planned !== null) return planned;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const elapsed = performance.now() - Number(visualizer.dataset.playStartedAt || "0");
  return Math.min(durationMs, Number(visualizer.dataset.playStartMs || "0") + elapsed);
}

export function audioProgressMs(visualizer: VisualizerElement): number | null {
  const audio = audioClockFor(visualizer);
  if (!audio) return null;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  return Math.min(durationMs, (Number(audio.currentTime) || 0) * 1000);
}

export function currentProgressMs(visualizer: VisualizerElement): number | null {
  const planned = liveProgressMs(visualizer);
  if (planned !== null) return planned;
  return Number(visualizer.dataset.progressMs || visualizer.dataset.cursorMs || "0");
}

export function handlePlaybackBoundary(
  visualizer: VisualizerElement,
  nextMs: number,
  deps: PlaybackControllerDependencies,
  options: { forceAudioPlay?: boolean } = {},
): boolean {
  const boundary = planPlaybackBoundary({
    nextMs,
    pass: activePlaybackPass(visualizer, deps),
    repeat: deps.repeatEnabledFor(visualizer),
    repeatPauseMs: repeatPauseDelayMs(visualizer),
  });
  if (boundary.kind === "continue") return false;
  if (boundary.kind === "loop") {
    if (boundary.repeatPauseMs > 0) {
      scheduleRepeatLoopPlayback(visualizer, deps, options, boundary.pass, boundary.repeatPauseMs);
    } else {
      restartLoopPlaybackNow(visualizer, deps, options, boundary.pass);
    }
    return true;
  }
  completePlayback(visualizer, deps);
  return true;
}

export function completePlayback(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const resetCursorMs = playbackCompletionCursor(activePlaybackPass(visualizer, deps));
  const preserveStatus = visualizer.dataset.preserveStatusOnPlaybackEnd === "true";
  stopProgressClock(visualizer, deps);
  deps.setCursor(visualizer, resetCursorMs, false, { updateAnchor: false });
  ensurePlaybackCursorVisible(visualizer, resetCursorMs);
  if (audioClockReady(visualizer)) {
    seekAudioClock(visualizer, resetCursorMs, Number(visualizer.dataset.durationMs || "0"));
  }
  if (preserveStatus) {
    deps.restoreStatus(ord);
  } else {
    deps.clearStatus(ord);
  }
  visualizer.dataset.preserveStatusOnPlaybackEnd = "false";
  window.__aqeActiveField = ord;
  deps.focusAndSendCommand(ord, "aqe:play-ended");
}

export function paintProgressFromClock(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): void {
  const generation = visualizer.__aqePlaybackGeneration ?? 0;
  const tick = (frameNowMs: number): void => {
    if (visualizer.__aqePlaybackGeneration !== generation) return;
    if (visualizer.dataset.playbackState !== "playing") return;
    const nextMs = liveProgressMs(visualizer, frameNowMs);
    if (nextMs === null) {
      startManualProgressClock(visualizer, Number(visualizer.dataset.cursorMs || "0"), deps);
      return;
    }
    if (handlePlaybackBoundary(visualizer, nextMs, deps)) {
      return;
    }
    ensurePlaybackCursorVisible(visualizer, nextMs);
    renderPlaybackCursor(
      visualizer,
      nextMs,
      Number(visualizer.dataset.durationMs || "0"),
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
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const clampedStartMs = durationMs ? clampProgressMs(visualizer, startMs) : Math.max(0, Number(startMs) || 0);
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
  pauseAudioClock(visualizer);
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  if (!durationMs) return;
  visualizer.__aqeAudioClockFallback = true;
  visualizer.dataset.playbackState = "playing";
  visualizer.dataset.progressClockMode = "manual";
  writePlaybackPass(visualizer, pass);
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  startPlaybackPlan(visualizer, clockStartMs, pass.endMs);
  paintProgressFromClock(visualizer, deps);
}

export function startAudioProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  deps: PlaybackControllerDependencies,
  options: ProgressClockOptions = {},
): void {
  const audio = audioClockFor(visualizer);
  if (!audio || !seekAudioClock(visualizer, startMs, Number(visualizer.dataset.durationMs || "0")) || typeof audio.play !== "function") {
    if (options.manualFallback === false) {
      options.onAudioPlayFailed?.();
      return;
    }
    startManualPlaybackPass(visualizer, activePlaybackPass(visualizer, deps), deps);
    return;
  }
  visualizer.dataset.progressClockMode = "audio";
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
    if (visualizer.dataset.playbackState !== "playing") return;
    clearPlaybackFrame(visualizer);
    visualizer.dataset.progressClockMode = "audio";
    startPlaybackPlan(visualizer, startMs, playbackEndMs(visualizer, deps));
    logger.info("html audio playback started", { ord: visualizer.dataset.aqeFieldOrd });
    paintProgressFromClock(visualizer, deps);
    options.onAudioStarted?.();
  };
  void Promise.resolve(audio.play())
    .then(startPainting)
    .catch(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      if (visualizer.dataset.playbackState !== "playing") return;
      logger.warn("html audio play rejected; using manual clock", { ord: visualizer.dataset.aqeFieldOrd });
      handlePlaybackFailure();
    });
}

export function startProgressClock(
  visualizer: VisualizerElement,
  startMs: number,
  deps: PlaybackControllerDependencies,
  options: ProgressClockOptions = {},
): void {
  const selectedEngine = options.engine || visualizer.dataset.playbackEngine || "";
  stopProgressClock(visualizer, deps, { clearEngine: false });
  deps.stopOtherPlayback(visualizer);
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const clampedStartMs = durationMs ? clampProgressMs(visualizer, startMs) : Math.max(0, Number(startMs) || 0);
  visualizer.dataset.playbackEngine = selectedEngine;
  visualizer.dataset.playbackState = "playing";
  visualizer.dataset.playStartedAt = String(performance.now());
  visualizer.dataset.playStartMs = String(clampedStartMs);
  const pass = setPlaybackPass(visualizer, clampedStartMs, deps);
  if (durationMs) {
    deps.setCursor(visualizer, clampedStartMs, false, { updateAnchor: false });
    ensurePlaybackCursorVisible(visualizer, clampedStartMs);
  } else {
    visualizer.dataset.cursorMs = String(Math.round(clampedStartMs));
    visualizer.dataset.progressMs = String(Math.round(clampedStartMs));
  }
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  logger.info("playback clock selected", { engine: selectedEngine || "auto", startMs: clampedStartMs });
  if (!durationMs) return;
  if (selectedEngine === "native") {
    startManualPlaybackPass(visualizer, pass, deps);
    return;
  }
  if (audioClockReady(visualizer)) {
    startAudioProgressClock(visualizer, clampedStartMs, deps, options);
    return;
  }
  if (options.manualFallback === false) {
    options.onAudioPlayFailed?.();
    return;
  }
  startManualPlaybackPass(visualizer, pass, deps);
}

export function pauseProgressClock(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): void {
  const currentMs = currentProgressMs(visualizer);
  if (currentMs !== null) {
    deps.setCursor(visualizer, currentMs, false, { updateAnchor: false });
  }
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  visualizer.dataset.playbackState = "paused";
  visualizer.dataset.progressClockMode = "stopped";
  deps.setPlaybackButtonLabel(visualizer, "Play");
}

export function stopProgressClock(
  visualizer: VisualizerElement,
  deps: PlaybackControllerDependencies,
  options: { clearAudio?: boolean; clearEngine?: boolean } = {},
): void {
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  visualizer.dataset.playbackState = "stopped";
  visualizer.dataset.progressClockMode = "stopped";
  visualizer.dataset.resumeRequiresRestart = "false";
  if (options.clearEngine !== false) {
    visualizer.dataset.playbackEngine = "";
  }
  if (options.clearAudio) {
    clearAudioClockSource(visualizer);
  }
  deps.setPlaybackButtonLabel(visualizer, "Play");
}

function scheduleRepeatLoopPlayback(
  visualizer: VisualizerElement,
  deps: PlaybackControllerDependencies,
  options: { forceAudioPlay?: boolean },
  pass: PlaybackPass,
  delayMs: number,
): void {
  const loopStartMs = pass.startMs;
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  writePlaybackPass(visualizer, pass);
  visualizer.dataset.playStartedAt = String(performance.now());
  visualizer.dataset.playStartMs = String(loopStartMs);
  visualizer.dataset.playbackState = "playing";
  visualizer.dataset.progressClockMode = "stopped";
  visualizer.dataset.repeatPauseWaiting = "true";
  deps.setCursor(visualizer, loopStartMs, false, { updateAnchor: false });
  ensurePlaybackCursorVisible(visualizer, loopStartMs);
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  startRepeatPauseCountdownOverlay(visualizer, delayMs);
  visualizer.__aqeRepeatPauseTimer = window.setTimeout(() => {
    visualizer.__aqeRepeatPauseTimer = null;
    clearRepeatPauseTimer(visualizer);
    if (visualizer.dataset.playbackState !== "playing") return;
    if (!deps.repeatEnabledFor(visualizer)) {
      completePlayback(visualizer, deps);
      return;
    }
    restartLoopPlaybackNow(visualizer, deps, { ...options, forceAudioPlay: true }, pass);
  }, delayMs);
}

function restartLoopPlaybackNow(
  visualizer: VisualizerElement,
  deps: PlaybackControllerDependencies,
  options: { forceAudioPlay?: boolean } = {},
  pass: PlaybackPass = activePlaybackPass(visualizer, deps),
): void {
  const loopStartMs = pass.startMs;
  clearRepeatPauseTimer(visualizer);
  writePlaybackPass(visualizer, pass);
  visualizer.dataset.playStartedAt = String(performance.now());
  visualizer.dataset.playStartMs = String(loopStartMs);
  visualizer.dataset.playbackState = "playing";
  deps.setCursor(visualizer, loopStartMs, false, { updateAnchor: false });
  ensurePlaybackCursorVisible(visualizer, loopStartMs);
  const canUseAudioClock = audioClockReady(visualizer)
    && (visualizer.dataset.progressClockMode === "audio" || visualizer.dataset.playbackEngine === "html");
  if (visualizer.dataset.progressClockMode !== "audio" || !audioClockReady(visualizer)) {
    if (!canUseAudioClock) {
      startManualPlaybackPass(visualizer, pass, deps);
      return;
    }
    visualizer.dataset.progressClockMode = "audio";
  }
  if (!seekAudioClock(visualizer, loopStartMs, Number(visualizer.dataset.durationMs || "0"))) {
    startManualPlaybackPass(visualizer, pass, deps);
    return;
  }
  if (!options.forceAudioPlay && visualizer.dataset.progressClockMode === "audio") {
    clearPlaybackFrame(visualizer);
    startPlaybackPlan(visualizer, loopStartMs, pass.endMs);
    paintProgressFromClock(visualizer, deps);
    return;
  }
  const audio = audioClockFor(visualizer);
  if (!audio || typeof audio.play !== "function") return;
  clearPlaybackFrame(visualizer);
  const playGeneration = visualizer.__aqePlaybackGeneration ?? 0;
  void Promise.resolve(audio.play())
    .then(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      if (visualizer.dataset.playbackState === "playing") {
        visualizer.dataset.progressClockMode = "audio";
        startPlaybackPlan(visualizer, loopStartMs, pass.endMs);
        paintProgressFromClock(visualizer, deps);
      }
    })
    .catch(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      if (visualizer.dataset.playbackState === "playing") {
        startManualPlaybackPass(visualizer, pass, deps);
      }
    });
}
