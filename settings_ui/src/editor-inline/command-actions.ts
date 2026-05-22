import { BUSY_COMMANDS, PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import { focusAndSendCommand, focusAndSendCommandPayload } from "./bridge.js";
import { allVisualizers } from "./dom-selectors.js";
import { logger } from "./logger.js";
import { requestGraph } from "./graph-actions.js";
import { buildSplitCommandPayload } from "./split-button-state.js";
import { rememberPostEditPlaybackIntent } from "./post-edit-playback.js";
import {
  handleHtmlPlaybackCommand,
  playbackStateFor,
  stopProgressClock,
} from "./playback-actions.js";
import type { EditorCommand, EditorCommandPayload, VisualizerElement } from "./types.js";
import { anyBusy, setControlsBusy } from "./control-actions.js";

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
  if (shouldPlayAfterSuccessfulEdit(command)) {
    rememberPostEditPlaybackIntent(ord);
  }
  if (BUSY_COMMANDS.has(command)) {
    stopAllEditorPlayback();
    setControlsBusy(ord, true, processingMessage(command, payload));
  }
  const effectivePayload =
    payload ??
    (command === "aqe:pitch-hum" || command === "aqe:share"
      ? buildSplitCommandPayload(command, ord)
      : undefined);
  if (effectivePayload) {
    focusAndSendCommandPayload(ord, effectivePayload);
    return;
  }
  focusAndSendCommand(ord, command);
}

function shouldPlayAfterSuccessfulEdit(command: EditorCommand): boolean {
  return PROCESSING_COMMANDS.has(command) || command === "aqe:undo" || command === "aqe:redo";
}

function stopAllEditorPlayback(): void {
  for (const visualizer of allVisualizers()) {
    if (playbackStateFor(visualizer as VisualizerElement) !== "stopped") {
      stopProgressClock(visualizer as VisualizerElement);
    }
  }
}
