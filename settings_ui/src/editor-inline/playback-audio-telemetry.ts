import type { VisualizerElement } from "./types.js";
import { audioClockReady } from "./audio-clock.js";
import {
  htmlAudioReadinessFor,
  type HtmlAudioReadinessReason,
  type HtmlAudioReadinessState,
} from "./audio-readiness.js";

export interface AudioClockTelemetry {
  audioClockAvailable: boolean;
  audioClockFallback: boolean;
  audioClockHasSrc: boolean;
  audioClockPresent: boolean;
  audioClockReady: boolean;
  audioClockReadyState: number | null;
  audioClockSrc: string;
  htmlAudioReadinessFailed: boolean;
  htmlAudioReadinessReason: HtmlAudioReadinessReason;
  htmlAudioReadinessState: HtmlAudioReadinessState;
  htmlAudioReadinessTransient: boolean;
}

export function audioClockTelemetryFor(visualizer: VisualizerElement | null): AudioClockTelemetry {
  const audio = visualizer?.querySelector<HTMLAudioElement>(".aqe-audio-clock") ?? null;
  const src = audio?.getAttribute("src") || "";
  const readyState = typeof audio?.readyState === "number" ? audio.readyState : null;
  const readiness = htmlAudioReadinessFor(visualizer);
  return {
    audioClockAvailable: !!visualizer?.__aqeAudioClockAvailable,
    audioClockFallback: !!visualizer?.__aqeAudioClockFallback,
    audioClockHasSrc: src.length > 0,
    audioClockPresent: !!audio,
    audioClockReady: audioClockReady(visualizer),
    audioClockReadyState: readyState,
    audioClockSrc: src,
    htmlAudioReadinessFailed: readiness.failed,
    htmlAudioReadinessReason: readiness.reason,
    htmlAudioReadinessState: readiness.state,
    htmlAudioReadinessTransient: readiness.transient,
  };
}

export function audioClockUnavailableReason(telemetry: AudioClockTelemetry): string {
  if (telemetry.htmlAudioReadinessReason) return telemetry.htmlAudioReadinessReason;
  if (!telemetry.audioClockPresent) return "audio_element_missing";
  if (!telemetry.audioClockHasSrc) return "audio_src_missing";
  if (!telemetry.audioClockAvailable) return "audio_clock_not_available";
  if (telemetry.audioClockReadyState !== null && telemetry.audioClockReadyState < 1) {
    return "audio_ready_state_below_metadata";
  }
  return "audio_clock_not_ready";
}
