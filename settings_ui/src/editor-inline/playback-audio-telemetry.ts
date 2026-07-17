import type { VisualizerElement } from "./types.js";
import {
  htmlAudioReadinessFor,
  type HtmlAudioReadinessReason,
  type HtmlAudioReadinessState,
} from "./audio-readiness.js";
import { readHtmlAudioPortSnapshot } from "./html-audio-session-controller.js";

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
  const ord = Number(visualizer?.dataset.aqeFieldOrd || "0");
  const port = readHtmlAudioPortSnapshot(ord);
  const readiness = htmlAudioReadinessFor(visualizer);
  return {
    audioClockAvailable: readiness.ready,
    audioClockFallback: readiness.failed,
    audioClockHasSrc: port.hasSource,
    audioClockPresent: port.present,
    audioClockReady: readiness.ready,
    audioClockReadyState: port.readyState,
    audioClockSrc: port.sourceUrl,
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
