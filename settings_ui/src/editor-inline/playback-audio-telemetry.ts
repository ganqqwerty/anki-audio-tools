import type { VisualizerElement } from "./types.js";
import { audioClockReady } from "./audio-clock.js";

export interface AudioClockTelemetry {
  audioClockAvailable: boolean;
  audioClockFallback: boolean;
  audioClockHasSrc: boolean;
  audioClockPresent: boolean;
  audioClockReady: boolean;
  audioClockReadyState: number | null;
  audioClockSrc: string;
}

export function audioClockTelemetryFor(visualizer: VisualizerElement | null): AudioClockTelemetry {
  const audio = visualizer?.querySelector<HTMLAudioElement>(".aqe-audio-clock") ?? null;
  const src = audio?.getAttribute("src") || "";
  const readyState = typeof audio?.readyState === "number" ? audio.readyState : null;
  return {
    audioClockAvailable: !!visualizer?.__aqeAudioClockAvailable,
    audioClockFallback: !!visualizer?.__aqeAudioClockFallback,
    audioClockHasSrc: src.length > 0,
    audioClockPresent: !!audio,
    audioClockReady: audioClockReady(visualizer),
    audioClockReadyState: readyState,
    audioClockSrc: src,
  };
}

export function audioClockUnavailableReason(telemetry: AudioClockTelemetry): string {
  if (!telemetry.audioClockPresent) return "audio_element_missing";
  if (!telemetry.audioClockHasSrc) return "audio_src_missing";
  if (!telemetry.audioClockAvailable) return "audio_clock_not_available";
  if (telemetry.audioClockReadyState !== null && telemetry.audioClockReadyState < 1) {
    return "audio_ready_state_below_metadata";
  }
  return "audio_clock_not_ready";
}
