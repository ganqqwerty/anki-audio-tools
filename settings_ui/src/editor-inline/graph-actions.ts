import type { ProsodyPayload } from "../lib/generated/contracts.js";
import { t } from "../lib/i18n.js";
import { isUserFacingError, type UserFacingError } from "../lib/user-facing-error.js";
import {
  clearPendingNoteScopedBridgeRequests,
  focusAndSendCommandPayload,
  sendGraphAnalysisRequest,
} from "./bridge.js";
import { finishDefaultGraphRequest } from "./default-graph-queue.js";
import { currentAudioSourceForOrd, visualizerForOrd } from "./dom-selectors.js";
import type { GraphSettings } from "./graph-settings.js";
import {
  audioFieldSource,
  editorRuntimeConfig,
} from "./editor-runtime-config.js";
import { logger } from "./logger.js";
import { normalizeTrack, type DefaultGraphTarget, type VisualizerElement } from "./types.js";
import { clearSourceMetadataRequests } from "./source-metadata-requests.js";
import {
  graphLogContext,
  renderGraphRequested,
  renderVisualizerStatus,
  renderVisualizerTrack,
  resetCursorProjection,
  resetVisualizerPlot,
} from "./visualizer-renderer.js";
import { resetLearnerRecordingState } from "./recording-actions.js";
import {
  audioClockReady,
  clearAudioClockSource,
  clearPlaybackFrame,
  clearSelection,
  configureAudioClock,
  seekAudioClock,
  setCursor,
  setRepeatEnabled,
  setSelection,
  stopProgressClock,
} from "./actions.js";
import {
  anyBusy,
  repeatDefaultFromConfig,
  setCommandButtonLabel,
  setControlsBusy,
  setHistoryAvailability,
  setStatusForOrd,
  setTransientStatusForOrd,
  updateButtonTooltipForDisabledState,
  clearStatus,
  hasStableStatusForOrd,
  restoreStatusForOrd,
} from "./control-actions.js";
import { graphSettingsForField } from "./graph-split-state.js";
import { resetVisualizerTimeViewport } from "./visualizer-state.js";
import { initFieldState, readFieldState, updateFieldState } from "./field-state-store.js";
import { initialFieldState } from "./field-state.js";

type EditorStatusMessage = string | UserFacingError;

let pendingGraphRedrawSettings: GraphSettings | null = null;

export function requestGraph(
  ord: number,
  notifyPython: boolean,
  graphSettings?: GraphSettings,
  sourceOverride?: string,
): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || !prepareGraphRequest(ord)) return;
  window.__aqeActiveField = ord;
  logger.info("graph requested", { notifyPython, ord });
  if (notifyPython) {
    setControlsBusy(ord, true, t("editor.status.analyzing"), "");
    const sourceFilename = sourceOverride || currentAudioSourceForOrd(ord);
    if (sourceFilename) {
      sendGraphAnalysisRequest({
        graphSettings: graphSettings ?? graphSettingsForField(ord),
        ord,
        sourceFilename,
      });
      return;
    }
    focusAndSendCommandPayload(ord, {
      command: "aqe:analyze",
      fieldOrd: ord,
      graphSettings: graphSettings ?? graphSettingsForField(ord),
    });
  }
}

export function requestDefaultGraph(target: DefaultGraphTarget): void {
  if (!prepareGraphRequest(target.ord)) return;
  logger.info("default graph requested", target);
  setControlsBusy(target.ord, true, t("editor.status.analyzing"), "");
  sendGraphAnalysisRequest({
    ...target,
    graphSettings: target.graphSettings ?? graphSettingsForField(target.ord),
  });
}

function prepareGraphRequest(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  stopProgressClock(visualizer, { clearAudio: true });
  resetLearnerRecordingState(ord);
  renderGraphRequested(visualizer);
  clearSelection(visualizer, { origin: "system" });
  setCursor(visualizer, 0, false);
  setCommandButtonLabel(ord, "aqe:analyze", "Redraw");
  setVisualizerStatus(ord, t("editor.status.analyzing"), "processing");
  return true;
}

export function resetGraphAfterEdit(
  ord: number,
  sourceFilename?: string | null,
  graphSettings?: GraphSettings | null,
): boolean {
  window.__aqePendingGraphRedrawField = ord;
  window.__aqePendingGraphRedrawSource = sourceFilename || null;
  pendingGraphRedrawSettings = graphSettings ?? null;
  return requestPendingGraphRedraw();
}

export function requestPendingGraphRedraw(): boolean {
  const ord = window.__aqePendingGraphRedrawField;
  if (typeof ord !== "number") return false;
  const expectedSource = window.__aqePendingGraphRedrawSource || "";
  const pendingSettings = pendingGraphRedrawSettings ?? undefined;
  const currentSource = currentAudioSourceForOrd(ord) || audioFieldSource(editorRuntimeConfig(), ord) || "";
  if (expectedSource && currentSource !== expectedSource) return false;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const s = readFieldState(ord);
  if (s.graph.busy) return true;
  if (s.graph.hasTrack && (!expectedSource || s.sourceFilename === expectedSource)) return true;
  requestGraph(ord, true, pendingSettings, expectedSource || undefined);
  return true;
}

function visualizerStatusText(message: EditorStatusMessage): string {
  return isUserFacingError(message) ? message.message : message;
}

export function setVisualizerStatus(ord: number, message: EditorStatusMessage, kind = "info"): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  renderVisualizerStatus(visualizer, visualizerStatusText(message), kind);
  setStatusForOrd(ord, message, kind, "", kind === "error" ? "error" : "graph");
}

export function setVisualizer(ord: number, rawTrack: ProsodyPayload, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || !rawTrack) return;
  const track = normalizeTrack(rawTrack);
  renderVisualizerTrack(visualizer, track);
  updateFieldState(ord, (state) => ({
    ...state,
    cursor: { ...state.cursor, anchorMs: 0 },
  }));
  if (pendingGraphRedrawMatches(ord, track.sourceFilename || "")) {
    window.__aqePendingGraphRedrawField = null;
    window.__aqePendingGraphRedrawSource = null;
    pendingGraphRedrawSettings = null;
  }
  setSelection(visualizer, 0, track.durationMs || 0, { origin: "system", updateCursor: false });
  configureAudioClock(visualizer, track.sourceFilename || "");
  setCommandButtonLabel(ord, "aqe:analyze", "Redraw");
  setCursor(visualizer, cursorMs || 0, false, { updateAnchor: false });
  if (audioClockReady(visualizer)) {
    seekAudioClock(visualizer, cursorMs || 0);
  }
  renderVisualizerStatus(visualizer, "", "info");
  setControlsBusy(ord, false, "", "");
  if (rawTrack.analysisWarning) {
    setTransientStatusForOrd(ord, rawTrack.analysisWarning, "warning", "graph");
    renderVisualizerStatus(visualizer, rawTrack.analysisWarning, "warning");
    if (hasStableStatusForOrd(ord)) {
      window.setTimeout(() => restoreStatusForOrd(ord), 4000);
    }
  }
  finishDefaultGraphRequest(ord, defaultGraphQueueDependencies());
  logger.info("graph rendered", graphLogContext(ord, track));
}

export function setVisualizerStatusFromPython(ord: number, message: EditorStatusMessage, kind = "info"): void {
  if (kind !== "processing" && window.__aqePendingGraphRedrawField === ord) {
    window.__aqePendingGraphRedrawField = null;
    window.__aqePendingGraphRedrawSource = null;
    pendingGraphRedrawSettings = null;
  }
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    visualizer.hidden = false;
    updateFieldState(ord, (state) => ({
      ...state,
      graph: {
        ...state.graph,
        active: true,
        hasTrack: kind === "processing" ? false : state.graph.hasTrack,
      },
    }));
    setCommandButtonLabel(ord, "aqe:analyze", "Redraw");
  }
  setVisualizerStatus(ord, message, kind);
  if (kind !== "processing") {
    finishDefaultGraphRequest(ord, defaultGraphQueueDependencies());
  }
}

export function defaultGraphQueueDependencies() {
  return {
    anyBusy,
    requestDefaultGraph,
  };
}

function pendingGraphRedrawMatches(ord: number, sourceFilename: string): boolean {
  if (window.__aqePendingGraphRedrawField !== ord) return false;
  const expectedSource = window.__aqePendingGraphRedrawSource || "";
  return !expectedSource || expectedSource === sourceFilename;
}

export function prepareForNewNote(): void {
  clearPendingNoteScopedBridgeRequests();
  clearSourceMetadataRequests();
  document.body.dataset.aqeBusy = "false";
  window.__aqeActiveField = null;
  window.__aqeLastCursorIntent = null;
  window.__aqeHistoryAvailabilityByField = {};
  document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => {
    controls.dataset.busy = "false";
    controls.dataset.aqeSourceFilename = "";
    const ord = Number(controls.dataset.aqeFieldOrd || "0");
    controls.querySelectorAll<HTMLButtonElement>(".aqe-button").forEach((button) => {
      button.disabled = button.dataset.aqeCommand === "aqe:undo" || button.dataset.aqeCommand === "aqe:redo";
      if (button.dataset.aqeCommand === "aqe:analyze") {
        setCommandButtonLabel(ord, "aqe:analyze", "Graph");
      }
      if (button.dataset.aqeCommand === "aqe:play") {
        setCommandButtonLabel(ord, "aqe:play", "Play");
      }
      updateButtonTooltipForDisabledState(button);
    });
    setHistoryAvailability(ord, false, false);
    clearStatus(ord);
    const visualizer = controls.querySelector<VisualizerElement>(".aqe-visualizer");
    if (!visualizer) return;
    clearPlaybackFrame(visualizer);
    clearAudioClockSource(visualizer);
    visualizer.hidden = true;
    initFieldState(ord, initialFieldState({ ord, repeatByDefault: repeatDefaultFromConfig() }));
    resetVisualizerTimeViewport(visualizer, 0);
    visualizer.dataset.targetDurationMs = "0";
    visualizer.dataset.learnerDurationMs = "0";
    visualizer.dataset.learnerRecordingStatus = "idle";
    visualizer.dataset.playStartedAt = "0";
    visualizer.dataset.playStartMs = "0";
    visualizer.dataset.playbackResetCursorMs = "0";
    visualizer.dataset.playbackLoop = "false";
    setRepeatEnabled(visualizer, repeatDefaultFromConfig());
    clearSelection(visualizer, { origin: "system" });
    resetVisualizerPlot(visualizer);
    resetCursorProjection(visualizer);
    resetLearnerRecordingState(ord);
    visualizer.dataset.statusMessage = "";
    const spinner = controls.querySelector<HTMLElement>(".aqe-spinner");
    if (spinner) spinner.hidden = true;
  });
}
