import { PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import { t } from "../lib/i18n.js";
import { focusAndSendCommand, focusAndSendCommandPayload } from "./bridge.js";
import { allVisualizers } from "./dom-selectors.js";
import { logger } from "./logger.js";
import { requestGraph } from "./graph-actions.js";
import { forgetPostEditPlaybackIntent, rememberPostEditPlaybackIntent } from "./post-edit-playback.js";
import {
  handleHtmlPlaybackCommand,
  playbackStateFor,
  stopProgressClock,
} from "./playback-actions.js";
import type { EditorCommand, EditorCommandPayload, VisualizerElement } from "./types.js";
import { anyBusy, setControlsBusy } from "./control-actions.js";
import { startLearnerRecordingCountdown } from "./recording-actions.js";

export function send(
  command: EditorCommand,
  node: HTMLElement,
  ord: number,
  payload?: EditorCommandPayload,
): void {
  if (anyBusy()) return;
  if (typeof node.focus === "function") node.focus();
  window.__aqeActiveField = ord;
  logger.info("command dispatched", { command, ord });
  if (command === "aqe:analyze") {
    requestGraph(ord, true, payload?.graphSettings);
    return;
  }
  if (command === "aqe:play" && handleHtmlPlaybackCommand(ord)) {
    return;
  }
  if (command === "aqe:record-voice") {
    stopAllEditorPlayback();
    if (startLearnerRecordingCountdown(node, ord)) {
      setControlsBusy(ord, true, t("editor.recording.countdown"), command);
    }
    return;
  }
  if (command === "aqe:play-recording") {
    stopAllEditorPlayback();
    focusAndSendCommand(ord, command);
    return;
  }
  if (isHistoryCommand(command)) {
    forgetPostEditPlaybackIntent(ord);
  }
  if (shouldPlayAfterSuccessfulEdit(command)) {
    rememberPostEditPlaybackIntent(ord);
  }
  if (PROCESSING_COMMANDS.has(command)) {
    stopAllEditorPlayback();
    setControlsBusy(ord, true, processingMessage(command));
  }
  if (payload) {
    focusAndSendCommandPayload(ord, payload);
    return;
  }
  focusAndSendCommand(ord, command);
}

function shouldPlayAfterSuccessfulEdit(command: EditorCommand): boolean {
  return PROCESSING_COMMANDS.has(command);
}

function isHistoryCommand(command: EditorCommand): boolean {
  return command === "aqe:undo" || command === "aqe:redo";
}

function stopAllEditorPlayback(): void {
  for (const visualizer of allVisualizers()) {
    if (playbackStateFor(visualizer as VisualizerElement) !== "stopped") {
      stopProgressClock(visualizer as VisualizerElement);
    }
  }
}
