import {
  audioClockFor,
  audioClockReady,
  clearAudioClockSource,
  pauseAudioClock,
  seekAudioClock,
} from "./audio-clock.js";
import { logger } from "./logger.js";
import type { PlaybackRegion } from "./playback-state.js";
import type { PlaybackState, VisualizerElement } from "./types.js";

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
}

export function manualProgressMs(visualizer: VisualizerElement): number {
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
  if (visualizer.dataset.progressClockMode === "audio") {
    return audioProgressMs(visualizer);
  }
  if (visualizer.dataset.progressClockMode === "manual") {
    return manualProgressMs(visualizer);
  }
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
  stopProgressClock(visualizer, deps);
  deps.setCursor(visualizer, anchorMs, false, { updateAnchor: false });
  if (audioClockReady(visualizer)) {
    seekAudioClock(visualizer, anchorMs, Number(visualizer.dataset.durationMs || "0"));
  }
  deps.clearStatus(ord);
  window.__aqeActiveField = ord;
  deps.focusAndSendCommand(ord, "aqe:play-ended");
}

export function paintProgressFromClock(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): void {
  const tick = (): void => {
    if (visualizer.dataset.playbackState !== "playing") return;
    const nextMs = audioProgressMs(visualizer);
    if (nextMs === null) {
      startManualProgressClock(visualizer, Number(visualizer.dataset.cursorMs || "0"), deps);
      return;
    }
    deps.setCursor(visualizer, nextMs, false, { updateAnchor: false });
    if (handlePlaybackBoundary(visualizer, nextMs, deps)) {
      return;
    }
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
  visualizer.dataset.playStartedAt = String(performance.now());
  visualizer.dataset.playStartMs = String(clampedStartMs);
  setPlaybackPass(visualizer, clampedStartMs, deps);
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  const tick = (): void => {
    if (visualizer.dataset.playbackState !== "playing") return;
    const nextMs = manualProgressMs(visualizer);
    deps.setCursor(visualizer, nextMs, false, { updateAnchor: false });
    if (handlePlaybackBoundary(visualizer, nextMs, deps)) {
      return;
    }
    visualizer.__aqePlaybackTimer = window.requestAnimationFrame(tick);
  };
  visualizer.__aqePlaybackTimer = window.requestAnimationFrame(tick);
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
  const handlePlaybackFailure = (): void => {
    if (options.manualFallback === false) {
      options.onAudioPlayFailed?.();
      return;
    }
    startManualProgressClock(visualizer, startMs, deps);
  };
  const startPainting = (): void => {
    if (visualizer.dataset.playbackState !== "playing") return;
    clearPlaybackFrame(visualizer);
    visualizer.dataset.progressClockMode = "audio";
    logger.info("html audio playback started", { ord: visualizer.dataset.aqeFieldOrd });
    paintProgressFromClock(visualizer, deps);
    options.onAudioStarted?.();
  };
  void Promise.resolve(audio.play())
    .then(startPainting)
    .catch(() => {
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
  if (!durationMs) return;
  const clampedStartMs = clampProgressMs(visualizer, startMs);
  visualizer.dataset.playbackEngine = selectedEngine;
  visualizer.dataset.playbackState = "playing";
  visualizer.dataset.playStartedAt = String(performance.now());
  visualizer.dataset.playStartMs = String(clampedStartMs);
  setPlaybackPass(visualizer, clampedStartMs, deps);
  deps.setCursor(visualizer, clampedStartMs, false, { updateAnchor: false });
  deps.setPlaybackButtonLabel(visualizer, "Pause");
  logger.info("playback clock selected", { engine: selectedEngine || "auto", startMs: clampedStartMs });
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
  const loopStartMs = region.startMs;
  setPlaybackPass(visualizer, loopStartMs, deps, region);
  visualizer.dataset.playStartedAt = String(performance.now());
  visualizer.dataset.playStartMs = String(loopStartMs);
  deps.setCursor(visualizer, loopStartMs, false, { updateAnchor: false });
  if (visualizer.dataset.progressClockMode !== "audio" || !audioClockReady(visualizer)) {
    startManualProgressClock(visualizer, loopStartMs, deps);
    return;
  }
  if (!seekAudioClock(visualizer, loopStartMs, Number(visualizer.dataset.durationMs || "0"))) {
    startManualProgressClock(visualizer, loopStartMs, deps);
    return;
  }
  if (!options.forceAudioPlay) {
    clearPlaybackFrame(visualizer);
    paintProgressFromClock(visualizer, deps);
    return;
  }
  const audio = audioClockFor(visualizer);
  if (!audio || typeof audio.play !== "function") return;
  clearPlaybackFrame(visualizer);
  void Promise.resolve(audio.play())
    .then(() => {
      if (visualizer.dataset.playbackState === "playing") {
        paintProgressFromClock(visualizer, deps);
      }
    })
    .catch(() => {
      if (visualizer.dataset.playbackState === "playing") {
        startManualProgressClock(visualizer, loopStartMs, deps);
      }
    });
}

function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}
