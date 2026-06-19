import { sendCommandPayload } from "./bridge.js";
import { allControls, visualizerForOrd } from "./dom-selectors.js";
import {
  editorRuntimeConfig,
  repeatPlaybackByDefault as configRepeatPlaybackByDefault,
} from "./editor-runtime-config.js";
import { requestGraph } from "./graph-actions.js";
import { logger } from "./logger.js";
import { readFieldState } from "./field-state-store.js";
import { isEditorBusy } from "./editor-control-state.js";
import { readRepeatPauseSecondsRuntime } from "./visualizer-runtime-state.js";
import type { EditorCommandPayload, PostEditPlaybackIntent } from "./types.js";
import {
  AUDIO_CLOCK_READINESS_CHANGED_EVENT,
  HTML_METADATA_WAIT_TIMEOUT_MS,
  htmlAudioReadinessFor,
  type AudioClockReadinessChangedDetail,
  type HtmlAudioReadiness,
} from "./audio-readiness.js";

const metadataWaitTimers: Map<number, number> = new Map();
const postEditGraphRequests: Set<string> = new Set();
const postEditReadyDispatches: Set<string> = new Set();

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
  const dispatchKey = postEditReadyDispatchKey(ord, pending, sourceFilename);
  if (postEditReadyDispatches.has(dispatchKey)) {
    logger.info("post-edit playback ready duplicate suppressed", postEditPlaybackDiagnosticContext(ord, sourceFilename));
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
  if (postEditShouldRequestRenderedGraph(ord, sourceFilename, readiness)) {
    postEditGraphRequests.add(postEditGraphRequestKey(ord, sourceFilename));
    requestGraph(ord, true, undefined, sourceFilename);
    logger.info("post-edit playback requested rendered graph for generated source", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  if (postEditRenderedGraphCanDriveHtmlPlayback(ord, sourceFilename, readiness)) {
    clearMetadataWaitTimer(ord);
    dispatchPostEditPlaybackReady({
      command: "aqe:post-edit-playback-ready",
      fieldOrd: ord,
      generation: pending.generation,
      sourceFilename,
    }, ord, sourceFilename, dispatchKey);
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
  }, ord, sourceFilename, dispatchKey);
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
  if (!detail) return;
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
    notifyPostEditPlaybackReady(ord, sourceFilename);
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
  postEditGraphRequests.clear();
  postEditReadyDispatches.clear();
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

export function postEditRenderedGraphCanDriveHtmlPlayback(
  ord: number,
  sourceFilename: string,
  readiness: HtmlAudioReadiness,
): boolean {
  if (readiness.reason !== "audio_metadata_loading") return false;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const state = readFieldState(ord);
  const sourceToMatch = sourceFilename || editorRuntimeConfig().pendingPostEditPlayback?.sourceFilename || "";
  return state.graph.hasTrack
    && state.graph.durationMs > 0
    && !!state.sourceFilename
    && (!sourceToMatch || state.sourceFilename === sourceToMatch);
}

function postEditShouldRequestRenderedGraph(
  ord: number,
  sourceFilename: string,
  readiness: HtmlAudioReadiness,
): boolean {
  if (!sourceFilename || !readiness.transient) return false;
  if (postEditGraphRequests.has(postEditGraphRequestKey(ord, sourceFilename))) return false;
  const pending = editorRuntimeConfig().pendingPostEditPlayback;
  if (pending?.requireGraphRedraw !== true && !sourceFilename.includes("__aqe_")) return false;
  const state = readFieldState(ord);
  if (pending?.requireGraphRedraw !== true && !state.graph.active && !state.graph.hasTrack) return false;
  if (state.graph.busy) return false;
  return !(state.graph.hasTrack && state.sourceFilename === sourceFilename);
}

function postEditGraphRequestKey(ord: number, sourceFilename: string): string {
  return `${ord}\u0000${sourceFilename}`;
}

function dispatchPostEditPlaybackReady(
  payload: EditorCommandPayload,
  ord: number,
  sourceFilename: string,
  dispatchKey: string,
): void {
  if (postEditReadyDispatches.has(dispatchKey)) return;
  postEditReadyDispatches.add(dispatchKey);
  clearMetadataWaitTimer(ord);
  postEditGraphRequests.delete(postEditGraphRequestKey(ord, sourceFilename));
  const testDispatcher = window.__aqeDispatchPostEditPlaybackReadyForTest;
  const dispatch = () => {
    sendCommandPayload(payload);
    logger.info("post-edit playback ready dispatched", postEditPlaybackDiagnosticContext(ord, sourceFilename));
  };
  if (testDispatcher?.(payload, dispatch) === true) return;
  dispatch();
}

function postEditReadyDispatchKey(
  ord: number,
  pending: NonNullable<ReturnType<typeof editorRuntimeConfig>["pendingPostEditPlayback"]>,
  sourceFilename: string,
): string {
  return `${ord}\u0000${pending.generation}\u0000${pending.sourceFilename || sourceFilename}`;
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
