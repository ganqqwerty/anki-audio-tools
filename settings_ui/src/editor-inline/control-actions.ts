import { PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import { t } from "../lib/i18n.js";
import {
  allButtons,
  buttonFor,
  controlsForOrd,
  graphButton,
  playButton,
} from "./dom-selectors.js";
import { continueDefaultGraphQueue } from "./default-graph-queue.js";
import { syncAllSelectionToolbars } from "./selection-toolbar-state.js";
import { setButtonTooltipContent, setTooltipContent } from "../lib/rich-tooltip.js";
import type { EditorCommand } from "./types.js";
import { defaultGraphQueueDependencies } from "./graph-actions.js";

export function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

export function repeatDefaultFromConfig(): boolean {
  return window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;
}

export function playRepeatOptionsTitle(enabled: boolean): string {
  return enabled ? t("editor.play.options_repeat_on") : t("editor.play.options_repeat_off");
}

export function setControlsBusy(ord: number, busy: boolean, message = "", command = ""): void {
  document.body.dataset.aqeBusy = busy ? "true" : "false";
  document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => {
    controls.dataset.busy = busy ? "true" : "false";
  });
  allButtons().forEach(updateButtonDisabledState);
  syncAllSelectionToolbars();
  if (!busy) {
    queueMicrotask(() => continueDefaultGraphQueue(defaultGraphQueueDependencies()));
  }
  const status = statusForOrd(ord);
  if (!status) return;
  if (busy) {
    renderStatus(status, message || "", "processing", command || "");
    return;
  }
  if (message || command) {
    setStatusForOrd(ord, message, "info", command);
    return;
  }
  restoreStableStatus(status);
}

export function setStatus(message: string, kind = "info"): void {
  const ord = Number(window.__aqeActiveField ?? 0);
  setStatusForOrd(ord, message, kind);
}

export function setStatusForOrd(ord: number, message: string, kind = "info", command = ""): void {
  const status = statusForOrd(ord);
  if (!status) return;
  if (kind !== "processing") {
    status.dataset.stableMessage = message || "";
    status.dataset.stableKind = kind || "info";
    status.dataset.stableCommand = command || "";
  }
  renderStatus(status, message || "", kind || "info", command || "");
}

export function clearStatus(ord: number): void {
  const status = statusForOrd(ord);
  if (!status) return;
  status.dataset.stableMessage = "";
  status.dataset.stableKind = "info";
  status.dataset.stableCommand = "";
  renderStatus(status, "", "info", "");
}

export function restoreStatusForOrd(ord: number): void {
  const status = statusForOrd(ord);
  if (!status) return;
  restoreStableStatus(status);
}

export function applyInitialStatusForOrd(ord: number): void {
  const initialStatuses = window.__AQE_EDITOR_CONFIG__?.initialStatusByField;
  const initialStatus = initialStatuses?.[ord];
  if (!initialStatus?.message) return;
  setStatusForOrd(ord, initialStatus.message, initialStatus.kind || "info");
  if (initialStatuses) {
    delete initialStatuses[ord];
  }
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
    setButtonTooltipContent(button, title);
  }
}

export function setHistoryAvailability(ord: number, canUndo: boolean, canRedo: boolean): void {
  if (!window.__aqeHistoryAvailabilityByField) {
    window.__aqeHistoryAvailabilityByField = {};
  }
  window.__aqeHistoryAvailabilityByField[ord] = { canRedo: !!canRedo, canUndo: !!canUndo };
  const controls = controlsForOrd(ord);
  if (controls) {
    controls.dataset.aqeCanUndo = canUndo ? "true" : "false";
    controls.dataset.aqeCanRedo = canRedo ? "true" : "false";
  }
  updateHistoryButtonState(ord, "aqe:undo");
  updateHistoryButtonState(ord, "aqe:redo");
}

export function historyAvailability(ord: number): { canRedo: boolean; canUndo: boolean } {
  return window.__aqeHistoryAvailabilityByField?.[ord] ?? { canRedo: false, canUndo: false };
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

function renderStatus(status: HTMLElement, message: string, kind: string, command: string): void {
  status.textContent = message;
  status.dataset.kind = kind;
  setTooltipContent(status, command);
}

function restoreStableStatus(status: HTMLElement): void {
  renderStatus(
    status,
    status.dataset.stableMessage || "",
    status.dataset.stableKind || "info",
    status.dataset.stableCommand || "",
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
  const title = available ? (enabledTitle || fallbackTitle) : disabledTitle;
  setButtonTooltipContent(button, title);
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
  button.disabled = busy;
}
