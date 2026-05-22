import type { ProsodyPayload } from "../lib/generated/contracts.js";
import { t } from "../lib/i18n.js";
import { focusAndSendCommandPayload, sendGraphAnalysisRequest } from "./bridge.js";
import { finishDefaultGraphRequest } from "./default-graph-queue.js";
import { currentAudioSourceForOrd, visualizerForOrd } from "./dom-selectors.js";
import type { GraphSettings } from "./graph-settings.js";
import { logger } from "./logger.js";
import { normalizeTrack, type DefaultGraphTarget, type VisualizerElement } from "./types.js";
import {
  graphLogContext,
  renderGraphRequested,
  renderVisualizerStatus,
  renderVisualizerTrack,
  resetCursorProjection,
  resetVisualizerPlot,
} from "./visualizer-renderer.js";
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
} from "./control-actions.js";
import { graphSettingsForField } from "./graph-split-state.js";

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
  renderGraphRequested(visualizer);
  clearSelection(visualizer);
  setCursor(visualizer, 0, false);
  setCommandButtonLabel(ord, "aqe:analyze", "Redraw");
  setVisualizerStatus(ord, t("editor.status.analyzing"), "processing");
  return true;
}

export function resetGraphAfterEdit(ord: number, sourceFilename?: string | null): boolean {
  window.__aqePendingGraphRedrawField = ord;
  window.__aqePendingGraphRedrawSource = sourceFilename || null;
  return requestPendingGraphRedraw();
}

export function requestPendingGraphRedraw(): boolean {
  const ord = window.__aqePendingGraphRedrawField;
  if (typeof ord !== "number") return false;
  const expectedSource = window.__aqePendingGraphRedrawSource || "";
  const currentSource = currentAudioSourceForOrd(ord) || window.__AQE_EDITOR_CONFIG__?.audioFieldSources?.[ord] || "";
  if (expectedSource && currentSource !== expectedSource) return false;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  if (visualizer.dataset.graphBusy === "true") return true;
  const renderedSource = visualizer.dataset.sourceFilename || "";
  if (visualizer.dataset.hasTrack === "true" && (!expectedSource || renderedSource === expectedSource)) return true;
  requestGraph(ord, true, undefined, expectedSource || undefined);
  return true;
}

export function setVisualizerStatus(ord: number, message: string, kind = "info"): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  renderVisualizerStatus(visualizer, message, kind);
}

export function setVisualizer(ord: number, rawTrack: ProsodyPayload, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || !rawTrack) return;
  const track = normalizeTrack(rawTrack);
  renderVisualizerTrack(visualizer, track);
  visualizer.dataset.anchorMs = String(cursorMs || 0);
  if (pendingGraphRedrawMatches(ord, track.sourceFilename || "")) {
    window.__aqePendingGraphRedrawField = null;
    window.__aqePendingGraphRedrawSource = null;
  }
  setSelection(visualizer, 0, track.durationMs || 0, { updateCursor: false });
  configureAudioClock(visualizer, track.sourceFilename || "");
  setCommandButtonLabel(ord, "aqe:analyze", "Redraw");
  setCursor(visualizer, cursorMs || 0, false);
  if (audioClockReady(visualizer)) {
    seekAudioClock(visualizer, cursorMs || 0);
  }
  setVisualizerStatus(ord, track.analyzerName || "", "info");
  setControlsBusy(ord, false, "", "");
  finishDefaultGraphRequest(ord, defaultGraphQueueDependencies());
  logger.info("graph rendered", graphLogContext(ord, track));
}

export function setVisualizerStatusFromPython(ord: number, message: string, kind = "info"): void {
  if (kind !== "processing" && window.__aqePendingGraphRedrawField === ord) {
    window.__aqePendingGraphRedrawField = null;
    window.__aqePendingGraphRedrawSource = null;
  }
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    visualizer.hidden = false;
    visualizer.dataset.graphActive = "true";
    if (kind === "processing") {
      visualizer.dataset.hasTrack = "false";
    }
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
  document.body.dataset.aqeBusy = "false";
  window.__aqeActiveField = null;
  window.__aqeLastCursorIntent = null;
  document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => {
    controls.dataset.busy = "false";
    controls.dataset.aqeSourceFilename = "";
    controls.querySelectorAll<HTMLButtonElement>(".aqe-button").forEach((button) => {
      button.disabled = false;
      if (button.dataset.aqeCommand === "aqe:analyze") {
        setCommandButtonLabel(Number(controls.dataset.aqeFieldOrd || "0"), "aqe:analyze", "Graph");
      }
      if (button.dataset.aqeCommand === "aqe:play") {
        setCommandButtonLabel(Number(controls.dataset.aqeFieldOrd || "0"), "aqe:play", "Play");
      }
    });
    const status = controls.querySelector<HTMLElement>(".aqe-status");
    if (status) {
      status.textContent = "";
      status.dataset.kind = "info";
      status.title = "";
    }
    const visualizer = controls.querySelector<VisualizerElement>(".aqe-visualizer");
    if (!visualizer) return;
    clearPlaybackFrame(visualizer);
    clearAudioClockSource(visualizer);
    visualizer.hidden = true;
    visualizer.dataset.anchorMs = "0";
    visualizer.dataset.cursorMs = "0";
    visualizer.dataset.progressMs = "0";
    visualizer.dataset.graphActive = "false";
    visualizer.dataset.graphBusy = "false";
    visualizer.dataset.hasTrack = "false";
    visualizer.dataset.playbackState = "stopped";
    visualizer.dataset.playbackEngine = "";
    visualizer.dataset.resumeRequiresRestart = "false";
    visualizer.dataset.durationMs = "0";
    visualizer.dataset.sourceFilename = "";
    visualizer.dataset.analyzerName = "";
    visualizer.dataset.playStartedAt = "0";
    visualizer.dataset.playStartMs = "0";
    visualizer.dataset.playbackStartMs = "0";
    visualizer.dataset.playbackEndMs = "0";
    visualizer.dataset.playbackRegionMode = "full";
    visualizer.dataset.progressClockMode = "stopped";
    setRepeatEnabled(visualizer, repeatDefaultFromConfig());
    clearSelection(visualizer);
    resetVisualizerPlot(visualizer);
    resetCursorProjection(visualizer);
    const graphStatus = visualizer.querySelector<HTMLElement>(".aqe-visualizer-status");
    if (graphStatus) {
      graphStatus.textContent = "";
      graphStatus.dataset.kind = "info";
    }
    const spinner = visualizer.querySelector<HTMLElement>(".aqe-spinner");
    if (spinner) spinner.hidden = true;
  });
}
