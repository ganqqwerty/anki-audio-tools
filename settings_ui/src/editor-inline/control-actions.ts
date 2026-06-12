import { PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import { t } from "../lib/i18n.js";
import {
  allButtons,
  buttonFor,
  controlsForOrd,
  graphButton,
  playButton,
  visualizerForOrd,
} from "./dom-selectors.js";
import { chorusingControlsForVisualizer } from "./chorusing-dom.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { continueDefaultGraphQueue } from "./default-graph-queue.js";
import { notifyMountedPostEditPlaybackReady } from "./post-edit-playback.js";
import { syncAllSelectionToolbars } from "./selection-toolbar-state.js";
import { errorHelpUrl } from "../lib/error-links.js";
import { openEditorExternalLink } from "./external-links.js";
import { setButtonTooltipContent, setTooltipContent } from "../lib/rich-tooltip.js";
import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
import { isUserFacingError, type UserFacingError } from "../lib/user-facing-error.js";
import {
  editorRuntimeConfig,
  repeatPlaybackByDefault as configRepeatPlaybackByDefault,
} from "./editor-runtime-config.js";
import type { EditorCommand, HistorySnapshot } from "./types.js";
import { defaultGraphQueueDependencies } from "./graph-actions.js";
import { syncAllRecordingControls, syncRecordingControls } from "./recording-actions.js";

export type InitialEditorStatus = { kind?: string; message: string };
export type StatusOwner = "edit" | "error" | "graph" | "playback";

type EditorStatusMessage = string | UserFacingError;

export function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

export function repeatDefaultFromConfig(): boolean {
  return configRepeatPlaybackByDefault(editorRuntimeConfig());
}

export function playRepeatOptionsTitle(enabled: boolean): string {
  return enabled ? t("editor.play.options_repeat_on") : t("editor.play.options_repeat_off");
}

export function setControlsBusy(ord: number, busy: boolean, message = "", command = ""): void {
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
  if (!busy) {
    queueMicrotask(() => continueDefaultGraphQueue(defaultGraphQueueDependencies()));
    queueMicrotask(notifyMountedPostEditPlaybackReady);
  }
  const status = statusForOrd(ord);
  if (!status) return;
  if (busy) {
    renderStatus(status, message || "", "processing", command || "", "graph");
    return;
  }
  if (message || command) {
    setStatusForOrd(ord, message, "info", command, "edit");
    return;
  }
  restoreStableStatus(status);
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
  const status = statusForOrd(ord);
  if (!status) return;
  if (storesStableStatus(owner)) {
    status.dataset.stableMessage = statusText(message || "");
    if (isUserFacingError(message)) {
      status.dataset.stableUserError = JSON.stringify(message);
    } else {
      delete status.dataset.stableUserError;
    }
    status.dataset.stableKind = kind || "info";
    status.dataset.stableCommand = command || "";
  }
  renderStatus(status, message || "", kind || "info", command || "", owner);
}

export function setTransientStatusForOrd(
  ord: number,
  message: EditorStatusMessage,
  kind = "info",
  owner: StatusOwner = "graph",
): void {
  const status = statusForOrd(ord);
  if (!status) return;
  renderStatus(status, message || "", kind || "info", "", owner);
}

export function hasStableStatusForOrd(ord: number): boolean {
  const status = statusForOrd(ord);
  return Boolean(status?.dataset.stableMessage || status?.dataset.stableUserError);
}

export function clearStatus(ord: number): void {
  const status = statusForOrd(ord);
  if (!status) return;
  status.dataset.stableMessage = "";
  delete status.dataset.stableUserError;
  status.dataset.stableKind = "info";
  status.dataset.stableCommand = "";
  renderStatus(status, "", "info", "", "edit");
}

export function clearPlaybackStatusForOrd(ord: number): void {
  const status = statusForOrd(ord);
  if (!status || status.dataset.statusOwner !== "playback") return;
  restoreStableStatus(status);
}

export function restoreStatusForOrd(ord: number): void {
  const status = statusForOrd(ord);
  if (!status) return;
  restoreStableStatus(status);
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
  const button = command === "aqe:play"
    ? playButton(ord)
    : command === "aqe:analyze"
      ? graphButton(ord)
      : controlsForOrd(ord)?.querySelector<HTMLButtonElement>(`[data-aqe-command="${command}"]`) ?? null;
  if (!button) return;
  const displayLabel = localizedButtonLabel(command, label);
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

export function emptyHistorySnapshot(): HistorySnapshot {
  return { canRedo: false, canUndo: false, redoItems: [], undoItems: [] };
}

export function setHistorySnapshot(ord: number, snapshot: HistorySnapshot): void {
  if (!window.__aqeHistorySnapshotsByField) {
    window.__aqeHistorySnapshotsByField = {};
  }
  const limit = Math.min(100, Math.max(1, Math.trunc(editorRuntimeConfig().editorHistorySize ?? 100)));
  const normalized = {
    canRedo: !!snapshot.canRedo,
    canUndo: !!snapshot.canUndo,
    redoItems: snapshot.redoItems.slice(0, limit),
    undoItems: snapshot.undoItems.slice(0, limit),
  };
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
  return window.__aqeHistorySnapshotsByField?.[ord] ?? emptyHistorySnapshot();
}

export function historyAvailability(ord: number): { canRedo: boolean; canUndo: boolean } {
  const snapshot = historySnapshot(ord);
  return { canRedo: snapshot.canRedo, canUndo: snapshot.canUndo };
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

function statusForOrd(ord: number): HTMLElement | null {
  return controlsForOrd(ord)?.querySelector<HTMLElement>(".aqe-status") ?? null;
}

function statusText(message: EditorStatusMessage): string {
  return isUserFacingError(message) ? message.message : message;
}

function defaultStatusOwner(kind: string): StatusOwner {
  if (kind === "error") return "error";
  if (kind === "processing") return "graph";
  return "edit";
}

function storesStableStatus(owner: StatusOwner): boolean {
  return owner === "edit" || owner === "error";
}

function renderStatusContent(status: HTMLElement, message: EditorStatusMessage): void {
  status.textContent = "";
  if (!isUserFacingError(message)) {
    status.textContent = message;
    return;
  }
  const code = document.createElement("span");
  code.className = "aqe-error-code";
  code.textContent = `${message.code}:`;
  const link = document.createElement("a");
  link.className = "aqe-error-help-link";
  link.href = errorHelpUrl(message.code);
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Help";
  link.addEventListener("click", (event) => openEditorExternalLink(event, link.href));
  status.append(code, ` ${message.message} `, link);
}

function renderStatus(
  status: HTMLElement,
  message: EditorStatusMessage,
  kind: string,
  command: string,
  owner: StatusOwner,
): void {
  renderStatusContent(status, message);
  status.dataset.kind = kind;
  status.dataset.statusOwner = owner;
  setTooltipContent(status, command);
  const spinner = status.closest<HTMLElement>(".aqe-status-row")?.querySelector<HTMLElement>(".aqe-spinner");
  if (spinner) spinner.hidden = kind !== "processing";
}

function restoreStableStatus(status: HTMLElement): void {
  let message: EditorStatusMessage = status.dataset.stableMessage || "";
  const rawUserError = status.dataset.stableUserError;
  if (rawUserError) {
    try {
      const parsed = JSON.parse(rawUserError) as unknown;
      if (isUserFacingError(parsed)) message = parsed;
    } catch {
      delete status.dataset.stableUserError;
    }
  }
  renderStatus(
    status,
    message,
    status.dataset.stableKind || "info",
    status.dataset.stableCommand || "",
    defaultStatusOwner(status.dataset.stableKind || "info"),
  );
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
  const hasPlayableTrack = visualizer.dataset.hasTrack === "true" && readVisualizerTargetDurationMs(visualizer) > 0;
  const canInitialize = controls.baseStartMs === null && hasPlayableTrack;
  button.disabled = busy || !(controls.canPractice || canInitialize);
}
