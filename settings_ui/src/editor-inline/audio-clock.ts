import type { AudioClockElement, VisualizerElement } from "./types.js";

export interface AudioClockHandlerCallbacks {
  onEndedDuringPlayback?: () => void;
  onErrorDuringPlayback?: () => void;
  onLoadedMetadata?: (durationMs: number) => void;
}

export function mediaUrlForFilename(filename: string): string {
  return encodeURIComponent(filename || "").replaceAll("%2F", "/");
}

export function audioClockFor(visualizer: VisualizerElement | null): AudioClockElement | null {
  return visualizer?.querySelector<AudioClockElement>(".aqe-audio-clock") ?? null;
}

export function resetAudioClockState(visualizer: VisualizerElement): void {
  visualizer.__aqeAudioClockAvailable = false;
  visualizer.__aqeAudioClockFallback = false;
  visualizer.__aqeAudioClockLastSeekedMs = 0;
  visualizer.dataset.progressClockMode = "stopped";
}

export function pauseAudioClock(visualizer: VisualizerElement): void {
  const audio = audioClockFor(visualizer);
  if (!audio || typeof audio.pause !== "function") return;
  try {
    audio.pause();
  } catch {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = true;
  }
}

export function clearAudioClockSource(visualizer: VisualizerElement): void {
  const audio = audioClockFor(visualizer);
  resetAudioClockState(visualizer);
  if (!audio) return;
  pauseAudioClock(visualizer);
  audio.removeAttribute("src");
  audio.src = "";
  try {
    audio.load();
  } catch {
    visualizer.__aqeAudioClockFallback = true;
  }
}

export function configureAudioClock(visualizer: VisualizerElement, filename: string): void {
  const audio = audioClockFor(visualizer);
  resetAudioClockState(visualizer);
  if (!audio) {
    visualizer.__aqeAudioClockFallback = true;
    return;
  }
  pauseAudioClock(visualizer);
  if (!filename) {
    clearAudioClockSource(visualizer);
    return;
  }
  audio.setAttribute("src", mediaUrlForFilename(filename));
  try {
    audio.load();
  } catch {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = true;
  }
}

export function installAudioClockHandlers(
  visualizer: VisualizerElement,
  callbacks: AudioClockHandlerCallbacks = {},
): void {
  const audio = audioClockFor(visualizer);
  if (!audio || audio.__aqeClockHandlersInstalled) return;
  audio.__aqeClockHandlersInstalled = true;
  audio.addEventListener("loadedmetadata", () => {
    if (!audio.getAttribute("src")) return;
    visualizer.__aqeAudioClockAvailable = true;
    visualizer.__aqeAudioClockFallback = false;
    const durationSeconds = Number(audio.duration);
    if (Number.isFinite(durationSeconds) && durationSeconds > 0) {
      callbacks.onLoadedMetadata?.(Math.round(durationSeconds * 1000));
    }
  });
  audio.addEventListener("error", () => {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = true;
    if (visualizer.dataset.playbackState === "playing" && visualizer.dataset.progressClockMode === "audio") {
      callbacks.onErrorDuringPlayback?.();
    }
  });
  audio.addEventListener("ended", () => {
    if (visualizer.dataset.playbackState === "playing") {
      callbacks.onEndedDuringPlayback?.();
    }
  });
  audio.addEventListener("seeked", () => {
    visualizer.__aqeAudioClockLastSeekedMs = Math.round((Number(audio.currentTime) || 0) * 1000);
  });
}

export function audioClockReady(visualizer: VisualizerElement | null): boolean {
  const audio = audioClockFor(visualizer);
  if (!audio || !visualizer?.__aqeAudioClockAvailable) return false;
  if (!audio.getAttribute("src")) return false;
  return audio.readyState === undefined || audio.readyState >= 1;
}

export function seekAudioClock(visualizer: VisualizerElement, ms: number, durationMs: number): boolean {
  const audio = audioClockFor(visualizer);
  if (!audio) return false;
  const clamped = Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
  try {
    audio.currentTime = clamped / 1000;
    visualizer.__aqeAudioClockLastSeekedMs = Math.round(clamped);
    return true;
  } catch {
    visualizer.__aqeAudioClockAvailable = false;
    visualizer.__aqeAudioClockFallback = true;
    return false;
  }
}
