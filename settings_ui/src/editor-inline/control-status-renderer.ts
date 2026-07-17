import { errorHelpUrl } from "../lib/error-links.js";
import { t } from "../lib/i18n.js";
import { setTooltipContent } from "../lib/rich-tooltip.js";
import { isUserFacingError } from "../lib/user-facing-error.js";
import {
  clearPlaybackWarningState,
  restoreStableStatusState,
  setPlaybackWarningState,
  stableStatusState,
  type EditorStatusMessage,
  type StatusOwner,
} from "./editor-control-state.js";
import { controlsForOrd } from "./dom-selectors.js";
import { openEditorExternalLink } from "./external-links.js";
import { executePlaybackRecovery } from "./playback-recovery-coordinator.js";

export function statusForOrd(ord: number): HTMLElement | null {
  return controlsForOrd(ord)?.querySelector<HTMLElement>(".aqe-status") ?? null;
}

export function playbackWarningForOrd(ord: number): HTMLElement | null {
  return controlsForOrd(ord)?.querySelector<HTMLElement>(".aqe-playback-warning") ?? null;
}

export function defaultStatusOwner(kind: string): StatusOwner {
  if (kind === "error") return "error";
  if (kind === "processing") return "graph";
  return "edit";
}

export function renderStatus(
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

export function projectStableStatus(status: HTMLElement, ord: number): void {
  const stable = stableStatusState(ord);
  status.dataset.stableMessage = statusText(stable.message);
  if (isUserFacingError(stable.message)) {
    status.dataset.stableUserError = JSON.stringify(stable.message);
  } else {
    delete status.dataset.stableUserError;
  }
  status.dataset.stableKind = stable.kind;
  status.dataset.stableCommand = stable.command;
}

export function restoreStableStatus(ord: number, status: HTMLElement): void {
  const restored = restoreStableStatusState(ord);
  projectStableStatus(status, ord);
  renderStatus(
    status,
    restored.message,
    restored.kind,
    restored.command,
    restored.owner,
  );
}

function statusText(message: EditorStatusMessage): string {
  return isUserFacingError(message) ? message.message : message;
}

function renderStatusContent(
  status: HTMLElement,
  message: EditorStatusMessage,
): void {
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
  if (!message.recovery) return;
  const action = document.createElement("button");
  action.className = "aqe-error-recovery-action";
  action.type = "button";
  const recovery = message.recovery;
  action.dataset.testid = `aqe-convert-to-mp3-${recovery.fieldOrd}`;
  action.textContent = t("editor.action.convert_to_mp3");
  action.addEventListener("click", () => {
    if (executePlaybackRecovery(recovery, action)) clearPlaybackWarning(recovery.fieldOrd);
  });
  status.append(" ", action);
}

export function renderPlaybackWarning(ord: number, message: EditorStatusMessage): void {
  const warning = playbackWarningForOrd(ord);
  setPlaybackWarningState(ord, message);
  if (!warning) return;
  renderStatusContent(warning, message);
  warning.dataset.kind = "warning";
  warning.hidden = message === "";
}

export function clearPlaybackWarning(ord: number): void {
  clearPlaybackWarningState(ord);
  const warning = playbackWarningForOrd(ord);
  if (!warning) return;
  warning.textContent = "";
  delete warning.dataset.kind;
  warning.hidden = true;
}
