import type { ProsodyPayload } from "../lib/generated/contracts.js";
import { t } from "../lib/i18n.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
import { focusAndSendCommand, focusAndSendCommandPayload } from "./bridge.js";
import { allControls, buttonFor, controlsForOrd, visualizerForOrd } from "./dom-selectors.js";
import { clearGraphCountdownOverlay, renderGraphCountdownOverlay } from "./graph-countdown-overlay.js";
import { graphSettingsForField } from "./graph-split-state.js";
import { renderCursor, clearLearnerVisualizerTrack, renderLearnerVisualizerTrack } from "./visualizer-renderer.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { getSplitButtonState } from "./split-button-state.js";
import type { LearnerPlaybackStatus, LearnerRecordingStatePayload, LearnerRecordingStatus } from "./recording-state.js";
import { normalizeTrack, type NormalizedProsodyTrack, type ProsodyPoint, type VisualizerElement } from "./types.js";

const RECORDING_BLOCKING_STATUSES = new Set<LearnerRecordingStatus>([
  "countdown",
  "recording",
  "stopping",
  "analyzing",
]);

export function dispatchLearnerRecordingPrimary(node: HTMLElement, ord: number): boolean {
  const status = learnerRecordingStatusForOrd(ord);
  if (status === "recording") {
    return stopLearnerRecording(node, ord);
  }
  if (status === "countdown" || status === "stopping" || status === "analyzing") {
    return false;
  }
  return startLearnerRecordingCountdown(node, ord);
}

export function startLearnerRecordingCountdown(node: HTMLElement, ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  const targetDurationMs = targetDurationForRecording(visualizer);
  if (!visualizer || targetDurationMs <= 0) return false;

  window.__aqeStopEditorPlayback?.(ord);
  clearLearnerVisualizerTrack(visualizer);
  delete visualizer.__aqeLearnerTrack;
  const startCursorMs = recordingStartCursorMs(visualizer, targetDurationMs);
  visualizer.dataset.learnerDurationMs = "0";
  visualizer.dataset.learnerStartCursorMs = String(startCursorMs);
  setRecordingCursor(visualizer, startCursorMs, targetDurationMs);

  const countdownSeconds = getSplitButtonState(ord).voiceRecordingCountdownSeconds;
  if (visualizer.__aqeRecordCountdownTimer) {
    window.clearTimeout(visualizer.__aqeRecordCountdownTimer);
    visualizer.__aqeRecordCountdownTimer = null;
  }
  const dispatch = (): void => {
    visualizer.__aqeRecordCountdownTimer = null;
    if (!recordingTargetReady(ord)) {
      resetLearnerRecordingState(ord);
      return;
    }
    clearRecordingCountdownOverlay(visualizer);
    if (typeof node.focus === "function") node.focus();
    window.__aqeActiveField = ord;
    focusAndSendCommandPayload(ord, {
      command: "aqe:record-voice",
      fieldOrd: ord,
      graphSettings: graphSettingsForField(ord),
      startCursorMs,
    });
  };
  if (countdownSeconds <= 0) {
    dispatch();
    return true;
  }
  let remaining = countdownSeconds;
  const tick = (): void => {
    if (remaining <= 0) {
      dispatch();
      return;
    }
    setLearnerRecordingState({
      fieldOrd: ord,
      status: "countdown",
      countdownSeconds: remaining,
      targetDurationMs,
    });
    remaining -= 1;
    visualizer.__aqeRecordCountdownTimer = window.setTimeout(tick, 1000);
  };
  tick();
  return true;
}

export function stopLearnerRecording(node: HTMLElement, ord: number): boolean {
  if (typeof node.focus === "function") node.focus();
  window.__aqeActiveField = ord;
  focusAndSendCommand(ord, "aqe:stop-recording");
  return true;
}

export function setLearnerRecordingState(payload: LearnerRecordingStatePayload): void {
  const ord = resolveFieldOrd(payload.fieldOrd);
  const controls = controlsForOrd(ord);
  if (!controls) return;
  const status = payload.status || "idle";
  controls.dataset.learnerRecordingStatus = status;
  controls.dataset.learnerRecordingGeneration = payload.generation == null ? "" : String(payload.generation);
  controls.dataset.learnerRecordingMediaFilename = payload.mediaFilename || "";
  controls.dataset.learnerRecordingFailureMessage = payload.failureMessage || "";
  controls.dataset.learnerPlaybackStatus = playbackStatusForPayload(payload);
  if (payload.startCursorMs != null) {
    controls.dataset.learnerStartCursorMs = String(payload.startCursorMs);
  } else if (status === "idle") {
    controls.dataset.learnerStartCursorMs = "0";
  }

  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    visualizer.dataset.learnerRecordingStatus = status;
    visualizer.dataset.learnerPlaybackStatus = playbackStatusForPayload(payload);
    if (payload.targetDurationMs != null) {
      visualizer.dataset.targetDurationMs = String(payload.targetDurationMs);
    }
    if (payload.startCursorMs != null) {
      visualizer.dataset.learnerStartCursorMs = String(payload.startCursorMs);
    } else if (status === "idle") {
      visualizer.dataset.learnerStartCursorMs = "0";
    }
    if (payload.recordingDurationMs != null) {
      visualizer.dataset.learnerDurationMs = String(payload.recordingDurationMs);
    }
    if (status === "recording") {
      startRecordingCursor(
        visualizer,
        payload.targetDurationMs ?? targetDurationForRecording(visualizer),
        learnerStartCursorMsForVisualizer(visualizer),
      );
    } else {
      stopRecordingCursor(visualizer);
    }
    renderRecordingCountdownOverlay(visualizer, payload);
  }
  renderRecordingStatus(controls, payload);
  syncRecordingControls(ord);
}

export function setLearnerVisualizer(ord: number, rawTrack: ProsodyPayload): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || !rawTrack) return;
  const track = normalizeTrack(rawTrack);
  renderLearnerVisualizerTrack(visualizer, offsetLearnerTrack(track, learnerStartCursorMsForVisualizer(visualizer)));
  syncRecordingControls(ord);
}

export function resetLearnerRecordingState(ord: number, options: { clearOverlay?: boolean } = {}): void {
  const visualizer = visualizerForOrd(ord);
  if (visualizer?.__aqeRecordCountdownTimer) {
    window.clearTimeout(visualizer.__aqeRecordCountdownTimer);
    visualizer.__aqeRecordCountdownTimer = null;
  }
  if (visualizer) {
    stopRecordingCursor(visualizer);
    if (options.clearOverlay !== false) {
      clearLearnerVisualizerTrack(visualizer);
      delete visualizer.__aqeLearnerTrack;
      visualizer.dataset.learnerDurationMs = "0";
      visualizer.dataset.learnerStartCursorMs = "0";
    }
  }
  setLearnerRecordingState({ fieldOrd: ord, status: "idle" });
}

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
  const recordButton = buttonFor(ord, "aqe:record-voice");
  const playButton = buttonFor(ord, "aqe:play-recording");
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

  if (recordButton) {
    const recording = status === "recording";
    recordButton.dataset.aqeButtonState = recording ? "recording" : "default";
    const label = recording ? t("editor.command.stop_recording.label") : t("editor.command.record_voice.label");
    const title = recording ? t("editor.command.stop_recording.title") : t("editor.command.record_voice.title");
    const reason = recordButton.disabled && !recording
      ? recordingDisabledReason({ blocking, bodyBusy, targetReady })
      : undefined;
    const tooltip = tooltipWithDisabledClarification(title, reason);
    recordButton.querySelector<HTMLElement>(".aqe-button-label")!.textContent = label;
    recordButton.setAttribute("aria-label", tooltip);
    recordButton.dataset.aqeEnabledTitle = title;
    recordButton.dataset.aqeDisabledTitle = t("editor.command.record_voice.disabled_title");
    setButtonTooltipContent(recordButton, tooltip);
  }
  if (playButton) {
    const playing = playbackStatus === "playing";
    playButton.dataset.aqeButtonState = playing ? "pause" : "default";
    const label = playing ? t("editor.command.pause_recording.label") : t("editor.command.play_recording.label");
    const title = playing ? t("editor.command.pause_recording.title") : t("editor.command.play_recording.title");
    const reason = status === "ready"
      ? undefined
      : recordingPlaybackDisabledReason({ blocking, bodyBusy });
    const tooltip = tooltipWithDisabledClarification(title, reason);
    playButton.querySelector<HTMLElement>(".aqe-button-label")!.textContent = label;
    playButton.dataset.aqeEnabledTitle = title;
    playButton.dataset.aqeDisabledTitle = t("editor.command.play_recording.disabled_title");
    playButton.setAttribute("aria-label", tooltip);
    setButtonTooltipContent(playButton, tooltip);
  }
  syncReadyRecordingActionButton(shareButton, status, blocking, bodyBusy, {
    disabledTitleKey: "editor.command.share_recording.disabled_title",
    titleKey: "editor.command.share_recording.title",
  });
  syncReadyRecordingActionButton(showButton, status, blocking, bodyBusy, {
    disabledTitleKey: "editor.command.show_recording_file.disabled_title",
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

function startRecordingCursor(visualizer: VisualizerElement, targetDurationMs: number, startCursorMs: number): void {
  stopRecordingCursor(visualizer);
  const durationMs = Math.max(0, Number(targetDurationMs) || targetDurationForRecording(visualizer));
  const startMs = Math.max(0, Math.min(Number(startCursorMs) || 0, durationMs));
  visualizer.__aqeRecordingStartedAt = performance.now();
  const tick = (): void => {
    const startedAt = visualizer.__aqeRecordingStartedAt ?? performance.now();
    const elapsedMs = Math.max(0, performance.now() - startedAt);
    setRecordingCursor(visualizer, Math.min(startMs + elapsedMs, durationMs), durationMs);
    visualizer.__aqeRecordingCursorFrame = window.requestAnimationFrame(tick);
  };
  tick();
}

function stopRecordingCursor(visualizer: VisualizerElement): void {
  if (visualizer.__aqeRecordingCursorFrame) {
    window.cancelAnimationFrame(visualizer.__aqeRecordingCursorFrame);
  }
  visualizer.__aqeRecordingCursorFrame = null;
  visualizer.__aqeRecordingStartedAt = null;
}

function setRecordingCursor(visualizer: VisualizerElement, ms: number, targetDurationMs: number): void {
  const clamped = Math.max(0, Math.min(Number(ms) || 0, targetDurationMs || 0));
  visualizer.dataset.cursorMs = String(Math.round(clamped));
  visualizer.dataset.progressMs = String(Math.round(clamped));
  renderCursor(visualizer, clamped, Number(visualizer.dataset.durationMs || targetDurationMs || "0"));
}

function renderRecordingStatus(controls: HTMLElement, payload: LearnerRecordingStatePayload): void {
  const statusNode = controls.querySelector<HTMLElement>(".aqe-status");
  if (!statusNode) return;
  const status = payload.status || "idle";
  const message = recordingStatusText(payload);
  if (status === "idle" && !message) {
    statusNode.textContent = statusNode.dataset.stableMessage || "";
    statusNode.dataset.kind = statusNode.dataset.stableKind || "info";
    return;
  }
  statusNode.textContent = message;
  statusNode.dataset.kind = status === "failed"
    ? "error"
    : RECORDING_BLOCKING_STATUSES.has(status)
      ? "processing"
      : "info";
}

function recordingStatusText(payload: LearnerRecordingStatePayload): string {
  if (payload.status === "countdown") {
    return t("editor.recording.countdown", { seconds: payload.countdownSeconds ?? 0 });
  }
  if (payload.status === "recording") return t("editor.recording.recording");
  if (payload.status === "stopping") return t("editor.recording.stopping");
  if (payload.status === "analyzing") return t("editor.status.analyzing");
  if (payload.status === "ready") return t("editor.recording.ready");
  if (payload.status === "failed") return payload.failureMessage || t("editor.recording.failed");
  return "";
}

function renderRecordingCountdownOverlay(
  visualizer: VisualizerElement,
  payload: LearnerRecordingStatePayload,
): void {
  const seconds = countdownOverlaySeconds(payload);
  if (seconds == null) {
    clearGraphCountdownOverlay(visualizer);
    return;
  }
  const message = t("editor.recording.countdown", { seconds });
  renderGraphCountdownOverlay(visualizer, seconds, message);
}

function clearRecordingCountdownOverlay(visualizer: VisualizerElement): void {
  clearGraphCountdownOverlay(visualizer);
}

function countdownOverlaySeconds(payload: LearnerRecordingStatePayload): number | null {
  if (payload.status !== "countdown") return null;
  const seconds = Number(payload.countdownSeconds);
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  return Math.round(seconds);
}

function recordingTargetReady(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  return targetDurationForRecording(visualizer) > 0;
}

function targetDurationForRecording(visualizer: VisualizerElement | null): number {
  if (!visualizer || visualizer.dataset.hasTrack !== "true") return 0;
  return readVisualizerTargetDurationMs(visualizer);
}

function recordingStartCursorMs(visualizer: VisualizerElement, targetDurationMs: number): number {
  return Math.max(0, Math.min(Number(visualizer.dataset.cursorMs || "0") || 0, targetDurationMs));
}

function learnerStartCursorMsForVisualizer(visualizer: VisualizerElement): number {
  return Math.max(0, Number(visualizer.dataset.learnerStartCursorMs || "0") || 0);
}

function offsetLearnerTrack(track: NormalizedProsodyTrack, startCursorMs: number): NormalizedProsodyTrack {
  if (startCursorMs <= 0) return track;
  return {
    ...track,
    durationMs: track.durationMs + startCursorMs,
    points: track.points.map((point): ProsodyPoint => [
      point[0] + startCursorMs,
      point[1],
      point[2],
      point[3],
    ]),
  };
}

function learnerRecordingStatusForOrd(ord: number): LearnerRecordingStatus {
  return learnerRecordingStatusForControls(controlsForOrd(ord));
}

function learnerRecordingStatusForControls(controls: HTMLElement | null): LearnerRecordingStatus {
  const status = controls?.dataset.learnerRecordingStatus;
  if (
    status === "countdown"
    || status === "recording"
    || status === "stopping"
    || status === "analyzing"
    || status === "ready"
    || status === "failed"
  ) {
    return status;
  }
  return "idle";
}

function playbackStatusForPayload(payload: LearnerRecordingStatePayload): LearnerPlaybackStatus {
  if (payload.playbackStatus === "playing" || payload.playbackStatus === "paused") {
    return payload.playbackStatus;
  }
  return "stopped";
}

function learnerPlaybackStatusForControls(controls: HTMLElement | null): LearnerPlaybackStatus {
  const status = controls?.dataset.learnerPlaybackStatus;
  if (status === "playing" || status === "paused") return status;
  return "stopped";
}

function syncReadyRecordingActionButton(
  button: HTMLButtonElement | null,
  status: LearnerRecordingStatus,
  blocking: boolean,
  bodyBusy: boolean,
  keys: { disabledTitleKey: string; titleKey: string },
): void {
  if (!button) return;
  const title = t(keys.titleKey);
  const reason = status === "ready"
    ? undefined
    : recordingPlaybackDisabledReason({ blocking, bodyBusy });
  const tooltip = tooltipWithDisabledClarification(title, reason);
  button.dataset.aqeEnabledTitle = title;
  button.dataset.aqeDisabledTitle = t(keys.disabledTitleKey);
  button.setAttribute("aria-label", tooltip);
  setButtonTooltipContent(button, tooltip);
}

function resolveFieldOrd(fieldOrd: number | null | undefined): number {
  if (typeof fieldOrd === "number" && Number.isFinite(fieldOrd)) return fieldOrd;
  return Number(window.__aqeActiveField ?? 0);
}

function toolbarButtonsForControls(controls: HTMLElement): HTMLButtonElement[] {
  const buttons: HTMLButtonElement[] = [];
  controls.childNodes.forEach((node) => {
    if (!(node instanceof HTMLElement)) return;
    if (node.matches(".aqe-button")) {
      buttons.push(node as HTMLButtonElement);
      return;
    }
    if (
      node.matches(".aqe-split-group")
      || node.matches(".aqe-split-button")
      || node.matches('[data-aqe-toolbar-button-container="true"]')
      || node.matches(".aqe-button-tooltip-target")
    ) {
      buttons.push(...Array.from(node.querySelectorAll<HTMLButtonElement>(".aqe-button")));
    }
  });
  return buttons;
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
