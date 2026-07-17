import type { VisualizerElement } from "./types.js";
import {
  readHtmlAudioPortSnapshot,
  readHtmlAudioSessionState,
} from "./html-audio-session-controller.js";
import type {
  HtmlAudioReadiness,
  HtmlAudioReadinessInput,
  HtmlAudioReadinessReason,
  HtmlAudioReadinessState,
} from "./html-audio-readiness-types.js";

export type {
  HtmlAudioReadiness,
  HtmlAudioReadinessInput,
  HtmlAudioReadinessReason,
  HtmlAudioReadinessState,
} from "./html-audio-readiness-types.js";

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
  if (!visualizer) return readiness("missing", "audio_element_missing");
  return htmlAudioReadinessForOrd(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function htmlAudioReadinessForOrd(ord: number): HtmlAudioReadiness {
  const state = readHtmlAudioSessionState(ord);
  const port = readHtmlAudioPortSnapshot(ord);
  if (state.kind === "failed") return readiness("failed", state.reason);
  if (!port.present) return readiness("missing", "audio_element_missing");
  if (state.kind === "empty" || !port.hasSource) return readiness("source_missing", "audio_src_missing");
  if (
    state.kind === "ready"
    || state.kind === "starting"
    || state.kind === "playing"
    || state.kind === "paused"
  ) {
    return readiness("ready", "audio_ready");
  }
  return readiness("loading_metadata", "audio_metadata_loading");
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
