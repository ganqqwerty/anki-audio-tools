import { allControls, currentAudioSourceForOrd, visualizerForOrd } from "./dom-selectors.js";
import {
  editorRuntimeConfig,
  repeatPlaybackByDefault as configRepeatPlaybackByDefault,
} from "./editor-runtime-config.js";
import { requestGraph } from "./graph-actions.js";
import { projectRepeatEnabled } from "./repeat-control-projection.js";
import { logger } from "./logger.js";
import { readFieldState } from "./field-state-store.js";
import { isEditorBusy } from "./editor-control-state.js";
import {
  readRepeatPauseSecondsRuntime,
  setRepeatPauseSecondsRuntime,
} from "./visualizer-runtime-state.js";
import type { PostEditPlaybackIntent } from "./types.js";
import { AutoplayKind, type PendingEditorAutoplay } from "../lib/generated/contracts.js";
import {
  htmlAudioSessionSourceFilename,
  readHtmlAudioSessionState,
} from "./html-audio-session-controller.js";
import type { HtmlAudioStartRequest } from "./html-audio-session-machine.js";
import { htmlAudioReadinessFor } from "./audio-readiness.js";
import {
  acceptPendingEditorIntent,
  failPendingEditorIntentForOrd,
} from "./editor-intent-controller.js";

class PostEditPlaybackRuntime {
  readonly graphRequests = new Set<string>();

  dispose(): void {
    this.graphRequests.clear();
  }
}

let activeRuntime: PostEditPlaybackRuntime | null = null;

function postEditRuntime(): PostEditPlaybackRuntime {
  activeRuntime ??= new PostEditPlaybackRuntime();
  return activeRuntime;
}

export function rememberPostEditPlaybackIntent(
  ord: number,
): Pick<PendingEditorAutoplay, "kind" | "repeatPauseMs"> {
  const visualizer = visualizerForOrd(ord);
  const s = visualizer ? readFieldState(ord) : null;
  const repeat = s ? s.playback.repeat : repeatDefaultFromConfig();
  const repeatPauseSeconds = normalizedRepeatPauseSeconds(
    visualizer ? readRepeatPauseSecondsRuntime(visualizer) : 0,
  );
  const backend = editorRuntimeConfig().backendEditorContext;
  logger.debug("post_edit.preference_remembered", {
    editorSessionId: backend?.editorSessionId ?? null,
    noteId: backend?.noteId ?? null,
    ord,
    repeat,
  });
  return {
    kind: repeat ? AutoplayKind.Repeat : AutoplayKind.Once,
    repeatPauseMs: Math.round(repeatPauseSeconds * 1000),
  };
}

export function postEditPlaybackIntentForOrd(ord: number): PostEditPlaybackIntent | null {
  const pending = editorRuntimeConfig().pendingEditorIntent;
  if (!pending || pending.target.fieldOrd !== ord) return null;
  return {
    repeat: pending.autoplay.kind === AutoplayKind.Repeat,
    repeatPauseSeconds: normalizedRepeatPauseSeconds(pending.autoplay.repeatPauseMs / 1000),
  };
}

export function notifyPostEditPlaybackReady(ord: number, sourceFilename: string): void {
  const pending = editorRuntimeConfig().pendingEditorIntent;
  if (!pending || pending.target.fieldOrd !== ord) return;
  if (pending.target.sourceFilename !== sourceFilename) {
    logger.warn("post-edit playback ready deferred: source mismatch", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  if (isEditorBusy()) {
    logger.info("post-edit playback ready deferred: editor busy", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  const readiness = postEditHtmlReadiness(ord);
  if (!readiness) {
    logger.info("post-edit playback ready deferred: visualizer missing", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  if (postEditShouldRequestRenderedGraph(ord, sourceFilename)) {
    postEditRuntime().graphRequests.add(postEditGraphRequestKey(ord, sourceFilename));
    requestGraph(ord, true, undefined, sourceFilename);
    logger.info("post-edit playback requested rendered graph for generated source", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  if (!postEditPlaybackGraphReady(ord, sourceFilename)) {
    logger.info("post-edit playback ready deferred: graph not ready", postEditPlaybackDiagnosticContext(ord, sourceFilename));
    return;
  }
  if (readiness.failed) {
    failPendingEditorIntentForOrd(ord);
    logger.warn("post-edit playback ready rejected: browser audio unavailable", {
      ...postEditPlaybackDiagnosticContext(ord, sourceFilename),
      htmlAudioReadinessReason: readiness.reason,
      htmlAudioReadinessState: readiness.state,
    });
    return;
  }
  if (readiness.ready) {
    acceptReadyPostEditIntent(ord, sourceFilename);
    return;
  }
  if (readiness.transient) {
    logger.info("post-edit playback ready deferred: browser audio loading", {
      ...postEditPlaybackDiagnosticContext(ord, sourceFilename),
      htmlAudioReadinessReason: readiness.reason,
      htmlAudioReadinessState: readiness.state,
    });
    return;
  }
}

function postEditPlaybackGraphReady(ord: number, sourceFilename: string): boolean {
  const pending = editorRuntimeConfig().pendingEditorIntent;
  if (!pending?.autoplay.requireGraphRedraw) return true;
  const sourceToMatch = pending.target.sourceFilename || sourceFilename;
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
      liveAudioSourceFilename(ord),
    );
  });
}

export function disposePostEditPlaybackReadiness(): void {
  activeRuntime?.dispose();
  activeRuntime = null;
}

export function resetPostEditPlaybackReadiness(): void {
  postEditRuntime().graphRequests.clear();
}

function postEditHtmlReadiness(ord: number) {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? htmlAudioReadinessFor(visualizer) : null;
}

function postEditPlaybackDiagnosticContext(ord: number, sourceFilename: string): Record<string, unknown> {
  const pending = editorRuntimeConfig().pendingEditorIntent;
  const visualizer = visualizerForOrd(ord);
  const s = visualizer ? readFieldState(ord) : null;
  return {
    bodyBusy: String(isEditorBusy()),
    controlSourceFilename: sourceFilename,
    graphBusy: s ? String(s.graph.busy) : "",
    hasPending: !!pending,
    hasTrack: s ? String(s.graph.hasTrack) : "",
    ord,
    pendingFieldOrd: pending?.target.fieldOrd,
    pendingDeliveryId: pending?.deliveryId,
    pendingRequireGraphRedraw: pending?.autoplay.requireGraphRedraw === true,
    pendingSourceFilename: pending?.target.sourceFilename || "",
    pendingSourceKind: pending?.sourceKind || "",
    sessionSourceFilename: htmlAudioSessionSourceFilename(ord),
    visualizerSourceFilename: s?.sourceFilename || "",
  };
}

function liveAudioSourceFilename(ord: number): string {
  return htmlAudioSessionSourceFilename(ord)
    || currentAudioSourceForOrd(ord)
    || readFieldState(ord).sourceFilename;
}

function postEditShouldRequestRenderedGraph(
  ord: number,
  sourceFilename: string,
): boolean {
  if (!sourceFilename) return false;
  if (postEditRuntime().graphRequests.has(postEditGraphRequestKey(ord, sourceFilename))) return false;
  const pending = editorRuntimeConfig().pendingEditorIntent;
  if (pending?.autoplay.requireGraphRedraw !== true && pending?.sourceKind !== "generated_edit") return false;
  const state = readFieldState(ord);
  if (pending?.autoplay.requireGraphRedraw !== true && !state.graph.active && !state.graph.hasTrack) return false;
  if (state.graph.busy) return false;
  return !(state.graph.hasTrack && state.sourceFilename === sourceFilename);
}

function postEditGraphRequestKey(ord: number, sourceFilename: string): string {
  return `${ord}\u0000${sourceFilename}`;
}

function acceptReadyPostEditIntent(
  ord: number,
  sourceFilename: string,
): void {
  postEditRuntime().graphRequests.delete(postEditGraphRequestKey(ord, sourceFilename));
  const pending = editorRuntimeConfig().pendingEditorIntent;
  if (!pending) return;
  acceptPendingEditorIntent({
    deliveryId: pending.deliveryId,
    editorSessionId: pending.target.editorSessionId,
    ord,
    request: postEditStartRequest(ord),
    sourceFilename,
  });
}

function postEditStartRequest(ord: number): HtmlAudioStartRequest {
  const retained = postEditPlaybackIntentForOrd(ord);
  const visualizer = visualizerForOrd(ord);
  if (retained && visualizer) {
    projectRepeatEnabled(visualizer, retained.repeat);
    setRepeatPauseSecondsRuntime(visualizer, retained.repeatPauseSeconds);
  }
  const field = readFieldState(ord);
  const session = readHtmlAudioSessionState(ord);
  const mediaDurationMs = "durationMs" in session ? session.durationMs : 0;
  return {
    cursorMs: field.playback.startMs,
    endMs: field.playback.regionMode === "selection"
      ? field.playback.endMs || mediaDurationMs
      : mediaDurationMs,
    loop: field.playback.repeat === true,
    ord,
    regionMode: field.playback.regionMode,
    resetCursorMs: field.playback.regionMode === "selection" && field.selection.startMs !== null
      ? Math.round(field.selection.startMs)
      : Math.round(field.cursor.anchorMs),
    source: "post_edit",
  };
}

function normalizedRepeatPauseSeconds(value: number): number {
  if (!Number.isFinite(value) || value <= 0) return 0;
  return Math.min(10, value);
}

function repeatDefaultFromConfig(): boolean {
  return configRepeatPlaybackByDefault(editorRuntimeConfig());
}
