import { sendCommandPayload } from "./bridge.js";
import { allControls, visualizerForOrd } from "./dom-selectors.js";
import {
  editorRuntimeConfig,
  repeatPlaybackByDefault as configRepeatPlaybackByDefault,
} from "./editor-runtime-config.js";
import { logger } from "./logger.js";
import { readFieldState } from "./field-state-store.js";
import { isEditorBusy } from "./editor-control-state.js";
import { readRepeatPauseSecondsRuntime } from "./visualizer-runtime-state.js";
import type { EditorCommandPayload, PostEditPlaybackIntent } from "./types.js";
import {
  AUDIO_CLOCK_READINESS_CHANGED_EVENT,
  HTML_METADATA_WAIT_TIMEOUT_MS,
  htmlAudioReadinessFor,
  markHtmlAudioFailure,
  type AudioClockReadinessChangedDetail,
} from "./audio-readiness.js";

const metadataWaitTimers: Map<number, number> = new Map();

export function rememberPostEditPlaybackIntent(ord: number): void {
  const visualizer = visualizerForOrd(ord);
  const s = visualizer ? readFieldState(ord) : null;
  postEditPlaybackIntents()[ord] = {
    repeat: s ? s.playback.repeat : repeatDefaultFromConfig(),
    repeatPauseSeconds: normalizedRepeatPauseSeconds(
      visualizer ? readRepeatPauseSecondsRuntime(visualizer) : 0,
    ),
  };
}

export function consumePostEditPlaybackIntent(ord: number): PostEditPlaybackIntent | null {
  const intents = postEditPlaybackIntents();
  const intent = intents[ord] ?? null;
  if (intent) {
    delete intents[ord];
  }
  return intent;
}

export function notifyPostEditPlaybackReady(ord: number, sourceFilename: string): void {
  const pending = editorRuntimeConfig().pendingPostEditPlayback;
  if (!pending || pending.fieldOrd !== ord) return;
  if (pending.sourceFilename && pending.sourceFilename !== sourceFilename) {
    logger.warn("post-edit playback ready deferred: source mismatch", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  if (isEditorBusy()) {
    logger.info("post-edit playback ready deferred: editor busy", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  if (!postEditPlaybackGraphReady(ord, sourceFilename)) {
    logger.info("post-edit playback ready deferred: graph not ready", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  const readiness = postEditHtmlReadiness(ord);
  if (!readiness) {
    logger.info("post-edit playback ready deferred: visualizer missing", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  if (readiness.transient) {
    ensureMetadataWaitTimer(ord, sourceFilename);
    logger.info("post-edit playback ready deferred: browser audio loading", {
      ...postEditPlaybackDiagnosticContext(ord, sourceFilename),
      htmlAudioReadinessReason: readiness.reason,
      htmlAudioReadinessState: readiness.state,
    });
    return;
  }
  clearMetadataWaitTimer(ord);
  dispatchPostEditPlaybackReady({
    command: "aqe:post-edit-playback-ready",
    fieldOrd: ord,
    generation: pending.generation,
    sourceFilename,
  }, ord, sourceFilename);
}

function postEditPlaybackGraphReady(ord: number, sourceFilename: string): boolean {
  const pending = editorRuntimeConfig().pendingPostEditPlayback;
  if (!pending?.requireGraphRedraw) return true;
  const sourceToMatch = pending.sourceFilename || sourceFilename;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const s = readFieldState(ord);
  return !s.graph.busy && s.graph.hasTrack
    && (!sourceToMatch || s.sourceFilename === sourceToMatch);
}

export function notifyMountedPostEditPlaybackReady(): void {
  allControls().forEach((controls) => {
    const ord = Number(controls.dataset.aqeFieldOrd || "0");
    notifyPostEditPlaybackReady(
      ord,
      readFieldState(ord).sourceFilename,
    );
  });
}

export function installPostEditPlaybackReadinessListener(): void {
  window.removeEventListener(AUDIO_CLOCK_READINESS_CHANGED_EVENT, handlePostEditReadinessChanged);
  window.addEventListener(AUDIO_CLOCK_READINESS_CHANGED_EVENT, handlePostEditReadinessChanged);
}

export function disposePostEditPlaybackReadiness(): void {
  window.removeEventListener(AUDIO_CLOCK_READINESS_CHANGED_EVENT, handlePostEditReadinessChanged);
  clearAllMetadataWaitTimers();
}

export function clearPostEditPlaybackReadinessTimers(): void {
  clearAllMetadataWaitTimers();
}

function handlePostEditReadinessChanged(event: Event): void {
  const detail = (event as CustomEvent<AudioClockReadinessChangedDetail>).detail;
  if (!detail || detail.readiness.transient) return;
  const pending = editorRuntimeConfig().pendingPostEditPlayback;
  if (!pending || pending.fieldOrd !== detail.ord) return;
  notifyPostEditPlaybackReady(detail.ord, readFieldState(detail.ord).sourceFilename);
}

function postEditHtmlReadiness(ord: number) {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? htmlAudioReadinessFor(visualizer) : null;
}

function ensureMetadataWaitTimer(ord: number, sourceFilename: string): void {
  if (metadataWaitTimers.has(ord)) return;
  const timer = window.setTimeout(() => {
    metadataWaitTimers.delete(ord);
    const visualizer = visualizerForOrd(ord);
    if (!visualizer) return;
    logger.warn("post-edit playback metadata wait timed out", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    markHtmlAudioFailure(visualizer, "metadata_timeout");
  }, HTML_METADATA_WAIT_TIMEOUT_MS);
  metadataWaitTimers.set(ord, timer);
}

function clearMetadataWaitTimer(ord: number): void {
  const timer = metadataWaitTimers.get(ord);
  if (timer === undefined) return;
  window.clearTimeout(timer);
  metadataWaitTimers.delete(ord);
}

function clearAllMetadataWaitTimers(): void {
  for (const timer of metadataWaitTimers.values()) {
    window.clearTimeout(timer);
  }
  metadataWaitTimers.clear();
}

function postEditPlaybackDiagnosticContext(ord: number, sourceFilename: string): Record<string, unknown> {
  const pending = editorRuntimeConfig().pendingPostEditPlayback;
  const visualizer = visualizerForOrd(ord);
  const s = visualizer ? readFieldState(ord) : null;
  return {
    bodyBusy: String(isEditorBusy()),
    controlSourceFilename: sourceFilename,
    graphBusy: s ? String(s.graph.busy) : "",
    hasPending: !!pending,
    hasTrack: s ? String(s.graph.hasTrack) : "",
    ord,
    pendingFieldOrd: pending?.fieldOrd,
    pendingGeneration: pending?.generation,
    pendingRequireGraphRedraw: pending?.requireGraphRedraw === true,
    pendingSourceFilename: pending?.sourceFilename || "",
    visualizerSourceFilename: s?.sourceFilename || "",
  };
}

function dispatchPostEditPlaybackReady(
  payload: EditorCommandPayload,
  ord: number,
  sourceFilename: string,
): void {
  clearMetadataWaitTimer(ord);
  const testDispatcher = window.__aqeDispatchPostEditPlaybackReadyForTest;
  const dispatch = () => {
    sendCommandPayload(payload);
    logger.info("post-edit playback ready dispatched", postEditPlaybackDiagnosticContext(ord, sourceFilename));
  };
  if (testDispatcher?.(payload, dispatch) === true) return;
  dispatch();
}

function postEditPlaybackIntents(): Record<number, PostEditPlaybackIntent> {
  window.__aqePostEditPlaybackIntents ??= {};
  return window.__aqePostEditPlaybackIntents;
}

function normalizedRepeatPauseSeconds(value: number): number {
  if (!Number.isFinite(value) || value <= 0) return 0;
  return Math.min(10, value);
}

function repeatDefaultFromConfig(): boolean {
  return configRepeatPlaybackByDefault(editorRuntimeConfig());
}
