import { PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import { t } from "../lib/i18n.js";
import {
  allButtons,
  buttonsFor,
  buttonFor,
  controlsForOrd,
  visualizerForOrd,
} from "./dom-selectors.js";
import { htmlAudioReadinessFor } from "./audio-readiness.js";
import { chorusingControlsForVisualizer } from "./chorusing-dom.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { continueDefaultGraphQueue } from "./default-graph-queue.js";
import { notifyMountedPostEditPlaybackReady } from "./post-edit-playback.js";
import { syncAllSelectionToolbars } from "./selection-toolbar-state.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
import {
  editorRuntimeConfig,
  repeatPlaybackByDefault as configRepeatPlaybackByDefault,
} from "./editor-runtime-config.js";
import type { EditorCommand, HistorySnapshot } from "./types.js";
import { defaultGraphQueueDependencies } from "./graph-actions.js";
import { syncAllRecordingControls, syncRecordingControls } from "./recording-actions.js";
import { readFieldState } from "./field-state-store.js";
import {
  clearStatusState,
  currentStatusState,
  emptyHistorySnapshot as emptyHistorySnapshotState,
  hasStableStatusState,
  historyAvailabilityState,
  historySnapshotState,
  isEditorBusy,
  restoreStableStatusState,
  setEditorBusy,
  setHistorySnapshotState,
  setStatusState,
  setTransientStatusState,
  type EditorStatusMessage,
  type StatusOwner,
} from "./editor-control-state.js";
import {
  defaultStatusOwner,
  projectStableStatus,
  renderStatus,
  restoreStableStatus,
  statusForOrd,
} from "./control-status-renderer.js";

export type InitialEditorStatus = { kind?: string; message: string };
export type { EditorStatusMessage, StatusOwner } from "./editor-control-state.js";
export { defaultStatusOwner } from "./control-status-renderer.js";

export function anyBusy(): boolean {
  return isEditorBusy();
}

export function repeatDefaultFromConfig(): boolean {
  return configRepeatPlaybackByDefault(editorRuntimeConfig());
}

export function playRepeatOptionsTitle(enabled: boolean): string {
  return enabled ? t("editor.play.options_repeat_on") : t("editor.play.options_repeat_off");
}

export function setControlsBusy(ord: number, busy: boolean, message = "", command = ""): void {
  setEditorBusy(busy);
  projectEditorBusyState();
  if (!busy) {
    queueMicrotask(() => continueDefaultGraphQueue(defaultGraphQueueDependencies()));
    queueMicrotask(notifyMountedPostEditPlaybackReady);
  }
  const status = statusForOrd(ord);
  if (busy) {
    const next = setStatusState(ord, message || "", "processing", command || "", "graph");
    if (!status) return;
    renderStatus(status, next.message, next.kind, next.command, next.owner);
    return;
  }
  if (message || command) {
    setStatusForOrd(ord, message, "info", command, "edit");
    return;
  }
  if (!status) {
    restoreStableStatusState(ord);
    return;
  }
  restoreStableStatus(ord, status);
}

export function projectEditorBusyState(): void {
  const busy = isEditorBusy();
  document.body.dataset.aqeBusy = busy ? "true" : "false";
  document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => {
    controls.dataset.busy = busy ? "true" : "false";
  });
  allButtons().forEach((button) => {
    updateButtonDisabledState(button);
    updateButtonTooltipForDisabledState(button);
  });
  syncAllRecordingControls();
  syncAllSelectionToolbars();
}

export function setStatus(message: EditorStatusMessage, kind = "info", owner: StatusOwner = defaultStatusOwner(kind)): void {
  const ord = Number(window.__aqeActiveField ?? 0);
  setStatusForOrd(ord, message, kind, "", owner);
}

export function setStatusForOrd(
  ord: number,
  message: EditorStatusMessage,
  kind = "info",
  command = "",
  owner: StatusOwner = defaultStatusOwner(kind),
): void {
  const next = setStatusState(ord, message, kind, command, owner);
  const status = statusForOrd(ord);
  if (!status) return;
  projectStableStatus(status, ord);
  renderStatus(status, next.message, next.kind, next.command, next.owner);
}

export function setTransientStatusForOrd(
  ord: number,
  message: EditorStatusMessage,
  kind = "info",
  owner: StatusOwner = "graph",
): void {
  const next = setTransientStatusState(ord, message, kind, owner);
  const status = statusForOrd(ord);
  if (!status) return;
  renderStatus(status, next.message, next.kind, next.command, next.owner);
}

export function hasStableStatusForOrd(ord: number): boolean {
  return hasStableStatusState(ord);
}

export function clearStatus(ord: number): void {
  const next = clearStatusState(ord);
  const status = statusForOrd(ord);
  if (!status) return;
  projectStableStatus(status, ord);
  renderStatus(status, next.message, next.kind, next.command, next.owner);
}

export function clearPlaybackStatusForOrd(ord: number): void {
  const status = statusForOrd(ord);
  if (currentStatusState(ord).owner !== "playback") return;
  if (!status) {
    restoreStableStatusState(ord);
    return;
  }
  restoreStableStatus(ord, status);
}

export function restoreStatusForOrd(ord: number): void {
  const status = statusForOrd(ord);
  if (!status) {
    restoreStableStatusState(ord);
    return;
  }
  restoreStableStatus(ord, status);
}

export function consumeInitialStatusForOrd(ord: number): InitialEditorStatus | null {
  const initialStatuses = editorRuntimeConfig().initialStatusByField;
  const initialStatus = initialStatuses?.[ord];
  if (initialStatuses) {
    delete initialStatuses[ord];
  }
  return initialStatus?.message ? initialStatus : null;
}

export function applyInitialHistoryAvailabilityForOrd(ord: number): void {
  const initialSnapshots = editorRuntimeConfig().initialHistorySnapshotsByField;
  const snapshot = initialSnapshots?.[ord];
  if (snapshot) {
    setHistorySnapshot(ord, snapshot);
    delete initialSnapshots[ord];
    return;
  }
  const initialAvailability = editorRuntimeConfig().initialHistoryAvailabilityByField;
  const availability = initialAvailability?.[ord];
  if (!availability) return;
  setHistoryAvailability(ord, availability.canUndo, availability.canRedo);
  delete initialAvailability[ord];
}

export function setCommandButtonLabel(ord: number, command: EditorCommand, label: string): void {
  const buttons = buttonsFor(ord, command);
  if (buttons.length === 0) return;
  const displayLabel = localizedButtonLabel(command, label);
  for (const button of buttons) {
    const labelNode = button.querySelector<HTMLElement>(".aqe-button-label");
    if (labelNode) {
      labelNode.textContent = displayLabel;
    } else {
      button.textContent = displayLabel;
    }
    if (command === "aqe:play") {
      button.dataset.aqeButtonState = label === "Pause" ? "pause" : "play";
    }
    if (command === "aqe:analyze") {
      button.dataset.aqeButtonState = label === "Redraw" ? "redraw" : "graph";
      const title = label === "Redraw" ? t("editor.command.redraw.title") : t("editor.command.graph.title");
      button.dataset.aqeEnabledTitle = title;
      setButtonTooltipContent(button, title);
    }
  }
}

export function emptyHistorySnapshot(): HistorySnapshot {
  return emptyHistorySnapshotState();
}

export function setHistorySnapshot(ord: number, snapshot: HistorySnapshot): void {
  const limit = Math.min(100, Math.max(1, Math.trunc(editorRuntimeConfig().editorHistorySize ?? 100)));
  const normalized = setHistorySnapshotState(ord, snapshot, limit);
  if (!window.__aqeHistorySnapshotsByField) {
    window.__aqeHistorySnapshotsByField = {};
  }
  window.__aqeHistorySnapshotsByField[ord] = normalized;
  if (!window.__aqeHistoryAvailabilityByField) {
    window.__aqeHistoryAvailabilityByField = {};
  }
  window.__aqeHistoryAvailabilityByField[ord] = {
    canRedo: normalized.canRedo,
    canUndo: normalized.canUndo,
  };
  const controls = controlsForOrd(ord);
  if (controls) {
    controls.dataset.aqeCanUndo = normalized.canUndo ? "true" : "false";
    controls.dataset.aqeCanRedo = normalized.canRedo ? "true" : "false";
  }
  updateHistoryButtonState(ord, "aqe:undo");
  updateHistoryButtonState(ord, "aqe:redo");
  syncRecordingControls(ord);
  window.dispatchEvent(new CustomEvent("aqe-history-snapshot", { detail: { ord } }));
}

export function setHistoryAvailability(ord: number, canUndo: boolean, canRedo: boolean): void {
  setHistorySnapshot(ord, {
    canRedo: !!canRedo,
    canUndo: !!canUndo,
    redoItems: [],
    undoItems: [],
  });
}

export function historySnapshot(ord: number): HistorySnapshot {
  return historySnapshotState(ord);
}

export function historyAvailability(ord: number): { canRedo: boolean; canUndo: boolean } {
  return historyAvailabilityState(ord);
}

function localizedButtonLabel(command: EditorCommand, label: string): string {
  if (command === "aqe:play" && label === "Pause") return t("editor.command.pause.label");
  if (command === "aqe:play" && label === "Play") return t("editor.command.play.label");
  if (command === "aqe:analyze" && label === "Redraw") return t("editor.command.redraw.label");
  if (command === "aqe:analyze" && label === "Graph") return t("editor.command.graph.label");
  return label;
}

export function processingBusyMessage(command: EditorCommand): string {
  return PROCESSING_COMMANDS.has(command) ? processingMessage(command) : "";
}

function updateHistoryButtonState(ord: number, command: "aqe:redo" | "aqe:undo"): void {
  const button = buttonFor(ord, command);
  if (!button) return;
  updateButtonDisabledState(button);
  const enabledTitle = button.dataset.aqeEnabledTitle || "";
  const fallbackTitle = button.getAttribute("aria-label") || "";
  const disabledTitle = button.dataset.aqeDisabledTitle || enabledTitle || fallbackTitle;
  const available = command === "aqe:undo" ? historyAvailability(ord).canUndo : historyAvailability(ord).canRedo;
  const reason = button.disabled
    ? (anyBusy() && available ? t("tooltip.disabled.editor_busy") : disabledTitle)
    : undefined;
  const title = tooltipWithDisabledClarification(enabledTitle || fallbackTitle, reason);
  setButtonTooltipContent(button, title);
}

export function updateButtonTooltipForDisabledState(button: HTMLButtonElement): void {
  const enabledTitle = button.dataset.aqeEnabledTitle || "";
  const fallbackTitle = baseTooltipTitle(button);
  const baseTitle = enabledTitle || fallbackTitle;
  if (!baseTitle) return;
  const reason = button.disabled
    ? (anyBusy() ? t("tooltip.disabled.editor_busy") : button.dataset.aqeDisabledTitle)
    : undefined;
  setButtonTooltipContent(button, tooltipWithDisabledClarification(baseTitle, reason));
}

function baseTooltipTitle(button: HTMLButtonElement): string {
  const currentTitle = button.getAttribute("data-aqe-tooltip-content") || button.getAttribute("aria-label") || "";
  return currentTitle.split(/\n\s*\n/, 1)[0]?.trim() ?? "";
}

function updateButtonDisabledState(button: HTMLButtonElement): void {
  const ord = Number(button.closest<HTMLElement>(".aqe-controls")?.dataset.aqeFieldOrd || "0");
  const busy = anyBusy();
  const command = button.dataset.aqeCommand;
  if (command === "aqe:play") {
    const visualizer = visualizerForOrd(ord);
    const readinessBlocksStart = readFieldState(ord).playback.state === "stopped"
      && htmlAudioReadinessFor(visualizer).transient;
    button.disabled = busy || readinessBlocksStart;
    if (readinessBlocksStart) {
      button.dataset.aqeDisabledTitle = t("tooltip.disabled.audio_metadata_loading");
    } else if (button.dataset.aqeDisabledTitle === t("tooltip.disabled.audio_metadata_loading")) {
      delete button.dataset.aqeDisabledTitle;
    }
    return;
  }
  if (command === "aqe:undo") {
    button.disabled = busy || !historyAvailability(ord).canUndo;
    return;
  }
  if (command === "aqe:redo") {
    button.disabled = busy || !historyAvailability(ord).canRedo;
    return;
  }
  if (
    command === "aqe:chorusing-practice"
    || command === "aqe:chorusing-next"
    || command === "aqe:chorusing-previous"
  ) {
    updateChorusingButtonDisabledState(button, ord, command, busy);
    return;
  }
  button.disabled = busy;
}

function updateChorusingButtonDisabledState(
  button: HTMLButtonElement,
  ord: number,
  command: "aqe:chorusing-practice" | "aqe:chorusing-next" | "aqe:chorusing-previous",
  busy: boolean,
): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) {
    button.disabled = true;
    return;
  }
  const controls = chorusingControlsForVisualizer(visualizer);
  if (command === "aqe:chorusing-next") {
    button.disabled = busy || !controls.canNext;
    return;
  }
  if (command === "aqe:chorusing-previous") {
    button.disabled = busy || !controls.canPrevious;
    return;
  }
  const hasPlayableTrack = readFieldState(ord).graph.hasTrack && readVisualizerTargetDurationMs(visualizer) > 0;
  const canInitialize = controls.baseStartMs === null && hasPlayableTrack;
  button.disabled = busy || !(controls.canPractice || canInitialize);
}
