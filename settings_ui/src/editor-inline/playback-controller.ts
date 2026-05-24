import {
  audioClockFor,
  audioClockReady,
  clearAudioClockSource,
  pauseAudioClock,
  seekAudioClock,
} from "./audio-clock.js";
import { logger } from "./logger.js";
import {
  playbackProgressPlan,
  progressMsForPlan,
} from "./playback-progress-clock.js";
import type { PlaybackRegion } from "./playback-state.js";
import type { PlaybackState, VisualizerElement } from "./types.js";
import { renderPlaybackCursor } from "./visualizer-renderer.js";

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

export function clearPlaybackFrame(visualizer: VisualizerElement): void {
  if (visualizer.__aqePlaybackTimer) {
    window.cancelAnimationFrame(visualizer.__aqePlaybackTimer);
    visualizer.__aqePlaybackTimer = null;
  }
  clearRepeatPauseTimer(visualizer);
  clearPlaybackPlan(visualizer);
  invalidatePlaybackFrames(visualizer);
}

function clearRepeatPauseTimer(visualizer: VisualizerElement): void {
  if (visualizer.__aqeRepeatPauseTimer) {
    window.clearTimeout(visualizer.__aqeRepeatPauseTimer);
    visualizer.__aqeRepeatPauseTimer = null;
  }
  visualizer.dataset.repeatPauseWaiting = "false";
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
  if (nextMs < playbackEndMs(visualizer, deps)) return false;
  if (deps.repeatEnabledFor(visualizer)) {
    restartLoopPlayback(visualizer, deps, options);
    return true;
  }
  completePlayback(visualizer, deps);
  return true;
}

export function completePlayback(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const region = deps.effectivePlaybackRegion(visualizer);
  const anchorMs = visualizer.dataset.playbackRegionMode === "selection"
    ? region.startMs
    : Number(visualizer.dataset.anchorMs || "0");
  const preserveStatus = visualizer.dataset.preserveStatusOnPlaybackEnd === "true";
  stopProgressClock(visualizer, deps);
  deps.setCursor(visualizer, anchorMs, false, { updateAnchor: false });
  if (audioClockReady(visualizer)) {
    seekAudioClock(visualizer, anchorMs, Number(visualizer.dataset.durationMs || "0"));
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
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  if (!durationMs) return;
  const clampedStartMs = clampProgressMs(visualizer, startMs);
  visualizer.__aqeAudioClockFallback = true;
  visualizer.dataset.playbackState = "playing";
  visualizer.dataset.progressClockMode = "manual";
  setPlaybackPass(visualizer, clampedStartMs, deps);
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  startPlaybackPlan(visualizer, clampedStartMs, playbackEndMs(visualizer, deps));
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
    startManualProgressClock(visualizer, startMs, deps);
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
    startManualProgressClock(visualizer, startMs, deps);
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
  setPlaybackPass(visualizer, clampedStartMs, deps);
  if (durationMs) {
    deps.setCursor(visualizer, clampedStartMs, false, { updateAnchor: false });
  } else {
    visualizer.dataset.cursorMs = String(Math.round(clampedStartMs));
    visualizer.dataset.progressMs = String(Math.round(clampedStartMs));
  }
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  logger.info("playback clock selected", { engine: selectedEngine || "auto", startMs: clampedStartMs });
  if (!durationMs) return;
  if (selectedEngine === "native") {
    startManualProgressClock(visualizer, clampedStartMs, deps);
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
  startManualProgressClock(visualizer, clampedStartMs, deps);
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

function setPlaybackPass(
  visualizer: VisualizerElement,
  startMs: number,
  deps: PlaybackControllerDependencies,
  region: PlaybackRegion = deps.effectivePlaybackRegion(visualizer),
): void {
  visualizer.dataset.playbackStartMs = String(Math.round(startMs));
  visualizer.dataset.playbackEndMs = String(Math.round(region.endMs));
  visualizer.dataset.playbackRegionMode = region.mode;
}

function playbackEndMs(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): number {
  const region = deps.effectivePlaybackRegion(visualizer);
  const endMs = Number(visualizer.dataset.playbackEndMs || "0") || region.endMs;
  return Math.max(region.startMs, Math.min(endMs, Number(visualizer.dataset.durationMs || "0") || 0));
}

function restartLoopPlayback(
  visualizer: VisualizerElement,
  deps: PlaybackControllerDependencies,
  options: { forceAudioPlay?: boolean } = {},
): void {
  const region = deps.effectivePlaybackRegion(visualizer);
  const delayMs = repeatPauseDelayMs(visualizer);
  if (delayMs > 0) {
    scheduleRepeatLoopPlayback(visualizer, deps, options, region, delayMs);
    return;
  }
  restartLoopPlaybackNow(visualizer, deps, options, region);
}

function scheduleRepeatLoopPlayback(
  visualizer: VisualizerElement,
  deps: PlaybackControllerDependencies,
  options: { forceAudioPlay?: boolean },
  region: PlaybackRegion,
  delayMs: number,
): void {
  const loopStartMs = region.startMs;
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  setPlaybackPass(visualizer, loopStartMs, deps, region);
  visualizer.dataset.playStartedAt = String(performance.now());
  visualizer.dataset.playStartMs = String(loopStartMs);
  visualizer.dataset.playbackState = "playing";
  visualizer.dataset.progressClockMode = "stopped";
  visualizer.dataset.repeatPauseWaiting = "true";
  deps.setCursor(visualizer, loopStartMs, false, { updateAnchor: false });
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  visualizer.__aqeRepeatPauseTimer = window.setTimeout(() => {
    visualizer.__aqeRepeatPauseTimer = null;
    visualizer.dataset.repeatPauseWaiting = "false";
    if (visualizer.dataset.playbackState !== "playing") return;
    if (!deps.repeatEnabledFor(visualizer)) {
      completePlayback(visualizer, deps);
      return;
    }
    restartLoopPlaybackNow(visualizer, deps, { ...options, forceAudioPlay: true }, region);
  }, delayMs);
}

function restartLoopPlaybackNow(
  visualizer: VisualizerElement,
  deps: PlaybackControllerDependencies,
  options: { forceAudioPlay?: boolean } = {},
  region: PlaybackRegion = deps.effectivePlaybackRegion(visualizer),
): void {
  const loopStartMs = region.startMs;
  clearRepeatPauseTimer(visualizer);
  setPlaybackPass(visualizer, loopStartMs, deps, region);
  visualizer.dataset.playStartedAt = String(performance.now());
  visualizer.dataset.playStartMs = String(loopStartMs);
  visualizer.dataset.playbackState = "playing";
  deps.setCursor(visualizer, loopStartMs, false, { updateAnchor: false });
  const canUseAudioClock = audioClockReady(visualizer)
    && (visualizer.dataset.progressClockMode === "audio" || visualizer.dataset.playbackEngine === "html");
  if (visualizer.dataset.progressClockMode !== "audio" || !audioClockReady(visualizer)) {
    if (!canUseAudioClock) {
      startManualProgressClock(visualizer, loopStartMs, deps);
      return;
    }
    visualizer.dataset.progressClockMode = "audio";
  }
  if (!seekAudioClock(visualizer, loopStartMs, Number(visualizer.dataset.durationMs || "0"))) {
    startManualProgressClock(visualizer, loopStartMs, deps);
    return;
  }
  if (!options.forceAudioPlay && visualizer.dataset.progressClockMode === "audio") {
    clearPlaybackFrame(visualizer);
    startPlaybackPlan(visualizer, loopStartMs, playbackEndMs(visualizer, deps));
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
        startPlaybackPlan(visualizer, loopStartMs, playbackEndMs(visualizer, deps));
        paintProgressFromClock(visualizer, deps);
      }
    })
    .catch(() => {
      if (visualizer.__aqePlaybackGeneration !== playGeneration) return;
      if (visualizer.dataset.playbackState === "playing") {
        startManualProgressClock(visualizer, loopStartMs, deps);
      }
    });
}

function startPlaybackPlan(visualizer: VisualizerElement, startMs: number, endMs: number): void {
  const nowMs = performance.now();
  const plan = playbackProgressPlan(startMs, endMs, nowMs);
  visualizer.__aqePlaybackGeneration = (visualizer.__aqePlaybackGeneration ?? 0) + 1;
  visualizer.__aqePlaybackPlan = plan;
  visualizer.__aqeLiveProgressMs = Math.round(plan.startMs);
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
  visualizer.dataset.playStartedAt = String(nowMs);
  visualizer.dataset.playStartMs = String(Math.round(plan.startMs));
  visualizer.dataset.progressMs = String(Math.round(plan.startMs));
}

function liveProgressMs(visualizer: VisualizerElement, nowMs: number = performance.now()): number | null {
  const plan = visualizer.__aqePlaybackPlan;
  if (!plan || visualizer.dataset.playbackState !== "playing") return null;
  const progressMs = progressMsForPlan(plan, nowMs);
  visualizer.__aqeLiveProgressMs = Math.round(progressMs);
  visualizer.dataset.progressMs = String(Math.round(progressMs));
  return progressMs;
}

function clearPlaybackPlan(visualizer: VisualizerElement): void {
  delete visualizer.__aqePlaybackPlan;
  delete visualizer.__aqeLiveProgressMs;
  delete visualizer.__aqeCursorPaintedAtMs;
  delete visualizer.__aqeCursorTextPaintedAtMs;
}

function invalidatePlaybackFrames(visualizer: VisualizerElement): void {
  visualizer.__aqePlaybackGeneration = (visualizer.__aqePlaybackGeneration ?? 0) + 1;
}

function repeatPauseDelayMs(visualizer: VisualizerElement): number {
  const seconds = Number(visualizer.dataset.repeatPauseSeconds || "0");
  if (!Number.isFinite(seconds) || seconds <= 0) return 0;
  return Math.round(Math.min(10, seconds) * 1000);
}

function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}
