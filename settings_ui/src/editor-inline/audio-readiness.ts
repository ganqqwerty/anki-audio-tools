import type { AudioClockElement, VisualizerElement } from "./types.js";

export const AUDIO_CLOCK_READINESS_CHANGED_EVENT = "aqe-audio-clock-readiness-changed";
export const HTML_METADATA_WAIT_TIMEOUT_MS = 5000;

export type HtmlAudioReadinessState = "failed" | "loading_metadata" | "missing" | "ready" | "source_missing";

export type HtmlAudioReadinessReason =
  | "audio_element_missing"
  | "audio_error"
  | "audio_load_failed"
  | "audio_metadata_loading"
  | "audio_pause_failed"
  | "audio_play_rejected"
  | "audio_ready"
  | "audio_seek_failed"
  | "audio_src_missing"
  | "metadata_timeout";

export interface HtmlAudioReadiness {
  failed: boolean;
  ready: boolean;
  reason: HtmlAudioReadinessReason;
  state: HtmlAudioReadinessState;
  transient: boolean;
}

export interface HtmlAudioReadinessInput {
  available: boolean;
  failureReason?: HtmlAudioReadinessReason | "";
  hasSrc: boolean;
  present: boolean;
  readyState: number | null;
}

export interface AudioClockReadinessChangedDetail {
  ord: number;
  readiness: HtmlAudioReadiness;
}

export function classifyHtmlAudioReadiness(input: HtmlAudioReadinessInput): HtmlAudioReadiness {
  if (input.failureReason) {
    return readiness("failed", input.failureReason);
  }
  if (!input.present) {
    return readiness("missing", "audio_element_missing");
  }
  if (!input.hasSrc) {
    return readiness("source_missing", "audio_src_missing");
  }
  if (input.readyState !== null && input.readyState >= 1) {
    return readiness("ready", "audio_ready");
  }
  if (input.available && input.readyState === null) {
    return readiness("ready", "audio_ready");
  }
  return readiness("loading_metadata", "audio_metadata_loading");
}

export function htmlAudioReadinessFor(visualizer: VisualizerElement | null): HtmlAudioReadiness {
  const audio = audioClockForReadiness(visualizer);
  return classifyHtmlAudioReadiness({
    available: !!visualizer?.__aqeAudioClockAvailable,
    failureReason: visualizer?.__aqeHtmlAudioFailureReason || "",
    hasSrc: !!audio?.getAttribute("src"),
    present: !!audio,
    readyState: typeof audio?.readyState === "number" ? audio.readyState : null,
  });
}

export function clearHtmlAudioFailure(visualizer: VisualizerElement): void {
  visualizer.__aqeHtmlAudioFailureReason = "";
  publishAudioReadinessChange(visualizer);
}

export function markHtmlAudioFailure(visualizer: VisualizerElement, reason: HtmlAudioReadinessReason): void {
  visualizer.__aqeHtmlAudioFailureReason = reason;
  visualizer.__aqeAudioClockAvailable = false;
  visualizer.__aqeAudioClockFallback = true;
  publishAudioReadinessChange(visualizer);
}

export function publishAudioReadinessChange(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const detail: AudioClockReadinessChangedDetail = {
    ord,
    readiness: htmlAudioReadinessFor(visualizer),
  };
  visualizer.dispatchEvent(new CustomEvent<AudioClockReadinessChangedDetail>(
    AUDIO_CLOCK_READINESS_CHANGED_EVENT,
    { bubbles: false, detail },
  ));
  window.dispatchEvent(new CustomEvent<AudioClockReadinessChangedDetail>(
    AUDIO_CLOCK_READINESS_CHANGED_EVENT,
    { detail },
  ));
}

function readiness(state: HtmlAudioReadinessState, reason: HtmlAudioReadinessReason): HtmlAudioReadiness {
  return {
    failed: state === "failed" || state === "missing",
    ready: state === "ready",
    reason,
    state,
    transient: state === "loading_metadata" || state === "source_missing",
  };
}

function audioClockForReadiness(visualizer: VisualizerElement | null): AudioClockElement | null {
  return visualizer?.querySelector<AudioClockElement>(".aqe-audio-clock") ?? null;
}
