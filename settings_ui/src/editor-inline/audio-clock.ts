import type { AudioClockElement, VisualizerElement } from "./types.js";
import { readFieldState, updateFieldState } from "./field-state-store.js";
import {
  clearHtmlAudioFailure,
  markHtmlAudioFailure,
  publishAudioReadinessChange,
} from "./audio-readiness.js";
import { logger } from "./logger.js";

export interface AudioClockHandlerCallbacks {
  onEndedDuringPlayback?: (durationMs: number) => void;
  onErrorDuringPlayback?: (cursorMs: number) => void;
  onLoadedMetadata?: (durationMs: number) => void;
}

export function mediaUrlForFilename(filename: string): string {
  return encodeURIComponent(filename || "").replaceAll("%2F", "/");
}

export function audioClockFor(visualizer: VisualizerElement | null): AudioClockElement | null {
  return visualizer?.querySelector<AudioClockElement>(".aqe-audio-clock") ?? null;
}

export function fieldPlaybackUsesAudioClock(ord: number): boolean {
  const field = readFieldState(ord);
  return field.playback.clockMode === "audio" && field.playback.state === "playing";
}

export function resetAudioClockState(visualizer: VisualizerElement): void {
  visualizer.__aqeAudioClockAvailable = false;
  visualizer.__aqeAudioClockFallback = false;
  visualizer.__aqeAudioClockLastSeekedMs = 0;
  visualizer.__aqeHtmlAudioFailureReason = "";
  updateFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"), (state) => ({
    ...state,
    playback: { ...state.playback, clockMode: "stopped" },
  }));
  publishAudioReadinessChange(visualizer);
}

export function installAudioClockHandlers(
  visualizer: VisualizerElement,
  callbacks: AudioClockHandlerCallbacks = {},
): void {
  const audio = audioClockFor(visualizer);
  if (!audio || audio.__aqeClockHandlersInstalled) return;
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  audio.__aqeClockHandlersInstalled = true;
  audio.addEventListener("loadedmetadata", () => {
    if (!audio.getAttribute("src")) return;
    visualizer.__aqeAudioClockAvailable = true;
    visualizer.__aqeAudioClockFallback = false;
    clearHtmlAudioFailure(visualizer);
    const durationSeconds = Number(audio.duration);
    logger.debug("audio_clock.loadedmetadata", {
      durationMs: Number.isFinite(durationSeconds) ? Math.round(durationSeconds * 1000) : null,
      ord,
      readyState: audio.readyState,
      src: audio.getAttribute("src") || "",
    });
    if (Number.isFinite(durationSeconds) && durationSeconds > 0) {
      callbacks.onLoadedMetadata?.(Math.round(durationSeconds * 1000));
    }
  });
  audio.addEventListener("error", () => {
    markHtmlAudioFailure(visualizer, "audio_error");
    logger.debug("audio_clock.error", {
      currentTimeMs: audioCurrentTimeMs(audio),
      errorCode: audio.error?.code ?? null,
      ord,
      readyState: audio.readyState,
      src: audio.getAttribute("src") || "",
    });
    callbacks.onErrorDuringPlayback?.(audioCurrentTimeMs(audio));
  });
  audio.addEventListener("play", () => {
    logger.debug("audio_clock.play", audioClockEventContext(audio, ord));
  });
  audio.addEventListener("playing", () => {
    logger.debug("audio_clock.playing", audioClockEventContext(audio, ord));
  });
  audio.addEventListener("pause", () => {
    logger.debug("audio_clock.pause", audioClockEventContext(audio, ord));
  });
  audio.addEventListener("ended", () => {
    logger.debug("audio_clock.ended", {
      ...audioClockEventContext(audio, ord),
      playbackState: readFieldState(ord).playback.state,
      repeatEnabled: readFieldState(ord).playback.repeat,
    });
    if (readFieldState(ord).playback.state === "playing") {
      callbacks.onEndedDuringPlayback?.(audioBoundaryDurationMs(audio));
    }
  });
  audio.addEventListener("seeked", () => {
    visualizer.__aqeAudioClockLastSeekedMs = Math.round((Number(audio.currentTime) || 0) * 1000);
  });
}

function audioClockEventContext(audio: AudioClockElement, ord: number): Record<string, unknown> {
  return {
    currentTimeMs: audioCurrentTimeMs(audio),
    durationMs: audioDurationMs(audio),
    ended: audio.ended,
    ord,
    paused: audio.paused,
    readyState: audio.readyState,
    src: audio.getAttribute("src") || "",
  };
}

function audioBoundaryDurationMs(audio: AudioClockElement): number {
  return Math.max(audioDurationMs(audio), audioCurrentTimeMs(audio));
}

function audioDurationMs(audio: AudioClockElement): number {
  const durationSeconds = Number(audio.duration);
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) return 0;
  return Math.round(durationSeconds * 1000);
}

function audioCurrentTimeMs(audio: AudioClockElement): number {
  const currentSeconds = Number(audio.currentTime);
  if (!Number.isFinite(currentSeconds) || currentSeconds <= 0) return 0;
  return Math.round(currentSeconds * 1000);
}

export function audioClockReady(visualizer: VisualizerElement | null): boolean {
  const audio = audioClockFor(visualizer);
  if (!audio) return false;
  if (!audio.getAttribute("src")) return false;
  return audio.readyState >= 1 || (audio.readyState === undefined && !!visualizer?.__aqeAudioClockAvailable);
}

export function seekAudioElementForCursorPreview(visualizer: VisualizerElement, ms: number, durationMs: number): boolean {
  const audio = audioClockFor(visualizer);
  if (!audio) return false;
  const clamped = Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
  try {
    audio.currentTime = clamped / 1000;
    visualizer.__aqeAudioClockLastSeekedMs = Math.round(clamped);
    return true;
  } catch {
    markHtmlAudioFailure(visualizer, "audio_seek_failed");
    return false;
  }
}
