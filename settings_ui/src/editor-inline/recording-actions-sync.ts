import { t } from "../lib/i18n.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { buttonTooltipContent, tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
import { allControls, buttonFor, buttonsFor, controlsForOrd } from "./dom-selectors.js";
import { recordingTargetReady, RECORDING_BLOCKING_STATUSES, learnerPlaybackStatusForControls, learnerRecordingStatusForControls } from "./recording-actions-state.js";

export function syncAllRecordingControls(): void {
  allControls().forEach((controls) => {
    syncRecordingControls(Number(controls.dataset.aqeFieldOrd || "0"));
  });
}

export function syncRecordingControls(ord: number): void {
  const controls = controlsForOrd(ord);
  if (!controls) return;
  const status = learnerRecordingStatusForControls(controls);
  const playbackStatus = learnerPlaybackStatusForControls(controls);
  const blocking = RECORDING_BLOCKING_STATUSES.has(status);
  const bodyBusy = document.body.dataset.aqeBusy === "true" || controls.dataset.busy === "true";
  const targetReady = recordingTargetReady(ord);
  const recordButtons = buttonsFor(ord, "aqe:record-voice");
  const playButtons = buttonsFor(ord, "aqe:play-recording");
  const shareButton = buttonFor(ord, "aqe:share-recording");
  const showButton = buttonFor(ord, "aqe:show-recording-file");

  toolbarButtonsForControls(controls).forEach((button) => {
    const command = button.dataset.aqeCommand || "";
    if (blocking) {
      button.disabled = !(command === "aqe:record-voice" && status === "recording");
      if (button.disabled) button.dataset.aqeRecordingDisabled = "true";
      return;
    }
    if (command === "aqe:record-voice") {
      button.disabled = bodyBusy || !targetReady;
      delete button.dataset.aqeRecordingDisabled;
    } else if (command === "aqe:play-recording") {
      button.disabled = bodyBusy || status !== "ready";
      delete button.dataset.aqeRecordingDisabled;
    } else if (command === "aqe:share-recording" || command === "aqe:show-recording-file") {
      button.disabled = bodyBusy || status !== "ready";
      delete button.dataset.aqeRecordingDisabled;
    } else if (button.dataset.aqeRecordingDisabled === "true") {
      button.disabled = buttonDisabledOutsideRecording(ord, command, bodyBusy);
      delete button.dataset.aqeRecordingDisabled;
    }
  });

  if (recordButtons.length > 0) {
    const recording = status === "recording";
    const label = recording ? t("editor.command.stop_recording.label") : t("editor.command.record_voice.label");
    const title = recording ? t("editor.command.stop_recording.title") : t("editor.command.record_voice.title");
    const enabledTitle = buttonTooltipContent(label, title);
    for (const recordButton of recordButtons) {
      recordButton.dataset.aqeButtonState = recording ? "recording" : "default";
      const reason = recordButton.disabled && !recording
        ? recordingDisabledReason({ blocking, bodyBusy, targetReady })
        : undefined;
      const tooltip = tooltipWithDisabledClarification(enabledTitle, reason);
      const recordLabel = recordButton.querySelector<HTMLElement>(".aqe-button-label");
      if (recordLabel) recordLabel.textContent = label;
      recordButton.setAttribute("aria-label", tooltip);
      recordButton.dataset.aqeEnabledTitle = enabledTitle;
      recordButton.dataset.aqeDisabledTitle = t("editor.command.record_voice.disabled_title");
      setButtonTooltipContent(recordButton, tooltip);
    }
  }
  if (playButtons.length > 0) {
    const playing = playbackStatus === "playing";
    const label = playing ? t("editor.command.pause_recording.label") : t("editor.command.play_recording.label");
    const title = playing ? t("editor.command.pause_recording.title") : t("editor.command.play_recording.title");
    const reason = status === "ready"
      ? undefined
      : recordingPlaybackDisabledReason({ blocking, bodyBusy });
    const enabledTitle = buttonTooltipContent(label, title);
    const tooltip = tooltipWithDisabledClarification(enabledTitle, reason);
    for (const playButton of playButtons) {
      playButton.dataset.aqeButtonState = playing ? "pause" : "default";
      const playLabel = playButton.querySelector<HTMLElement>(".aqe-button-label");
      if (playLabel) playLabel.textContent = label;
      playButton.dataset.aqeEnabledTitle = enabledTitle;
      playButton.dataset.aqeDisabledTitle = t("editor.command.play_recording.disabled_title");
      playButton.setAttribute("aria-label", tooltip);
      setButtonTooltipContent(playButton, tooltip);
    }
  }
  syncReadyRecordingActionButton(shareButton, status, blocking, bodyBusy, {
    disabledTitleKey: "editor.command.share_recording.disabled_title",
    labelKey: "editor.command.share_recording.label",
    titleKey: "editor.command.share_recording.title",
  });
  syncReadyRecordingActionButton(showButton, status, blocking, bodyBusy, {
    disabledTitleKey: "editor.command.show_recording_file.disabled_title",
    labelKey: "editor.command.show_recording_file.label",
    titleKey: "editor.command.show_recording_file.title",
  });
}

function recordingDisabledReason({
  blocking,
  bodyBusy,
  targetReady,
}: {
  blocking: boolean;
  bodyBusy: boolean;
  targetReady: boolean;
}): string {
  if (blocking) return t("tooltip.disabled.recording_active");
  if (bodyBusy) return t("tooltip.disabled.editor_busy");
  if (!targetReady) return t("editor.command.record_voice.disabled_title");
  return "";
}

function recordingPlaybackDisabledReason({
  blocking,
  bodyBusy,
}: {
  blocking: boolean;
  bodyBusy: boolean;
}): string {
  if (blocking) return t("tooltip.disabled.recording_active");
  if (bodyBusy) return t("tooltip.disabled.editor_busy");
  return t("editor.command.play_recording.disabled_title");
}

function syncReadyRecordingActionButton(
  button: HTMLButtonElement | null,
  status: string,
  blocking: boolean,
  bodyBusy: boolean,
  keys: { disabledTitleKey: string; labelKey: string; titleKey: string },
): void {
  if (!button) return;
  const label = t(keys.labelKey);
  const title = t(keys.titleKey);
  const reason = status === "ready"
    ? undefined
    : recordingPlaybackDisabledReason({ blocking, bodyBusy });
  const enabledTitle = buttonTooltipContent(label, title);
  const tooltip = tooltipWithDisabledClarification(enabledTitle, reason);
  button.dataset.aqeEnabledTitle = enabledTitle;
  button.dataset.aqeDisabledTitle = t(keys.disabledTitleKey);
  button.setAttribute("aria-label", tooltip);
  setButtonTooltipContent(button, tooltip);
}

function toolbarButtonsForControls(controls: HTMLElement): HTMLButtonElement[] {
  return Array.from(controls.querySelectorAll<HTMLButtonElement>(".aqe-button[data-aqe-command]"));
}

function buttonDisabledOutsideRecording(ord: number, command: string, bodyBusy: boolean): boolean {
  if (command === "aqe:undo") {
    return bodyBusy || !window.__aqeHistoryAvailabilityByField?.[ord]?.canUndo;
  }
  if (command === "aqe:redo") {
    return bodyBusy || !window.__aqeHistoryAvailabilityByField?.[ord]?.canRedo;
  }
  return bodyBusy;
}
