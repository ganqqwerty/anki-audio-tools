import { PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import { t } from "../lib/i18n.js";
import {
  allButtons,
  controlsForOrd,
  graphButton,
  playButton,
} from "./dom-selectors.js";
import { continueDefaultGraphQueue } from "./default-graph-queue.js";
import { syncAllSelectionToolbars } from "./selection-toolbar-state.js";
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
  allButtons().forEach((button) => {
    button.disabled = !!busy;
  });
  syncAllSelectionToolbars();
  if (!busy) {
    queueMicrotask(() => continueDefaultGraphQueue(defaultGraphQueueDependencies()));
  }
  const controls = controlsForOrd(ord);
  const status = controls?.querySelector<HTMLElement>(".aqe-status");
  if (!status) return;
  status.textContent = message || "";
  status.dataset.kind = busy ? "processing" : "info";
  status.title = command || "";
}

export function setStatus(message: string, kind = "info"): void {
  const ord = Number(window.__aqeActiveField ?? 0);
  const controls = controlsForOrd(ord);
  const status = controls?.querySelector<HTMLElement>(".aqe-status");
  if (!status) return;
  status.textContent = message || "";
  status.dataset.kind = kind || "info";
}

export function clearStatus(ord: number): void {
  const controls = controlsForOrd(ord);
  const status = controls?.querySelector<HTMLElement>(".aqe-status");
  if (!status) return;
  status.textContent = "";
  status.dataset.kind = "info";
  status.title = "";
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
    button.title = title;
    button.setAttribute("aria-label", title);
  }
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
