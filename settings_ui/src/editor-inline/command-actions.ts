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
import {
  moveChorusingForOrd,
  pauseChorusingForNormalPlay,
  toggleChorusingForOrd,
} from "./chorusing-controller.js";
import { toggleLearnerRecordingHtmlPlayback } from "./learner-recording-playback.js";
import type { EditorCommand, EditorCommandPayload } from "./types.js";
import { anyBusy, setControlsBusy } from "./control-actions.js";
import { editorRuntimeConfig } from "./editor-runtime-config.js";

type EditorDispatchCommand = EditorCommand | "aqe:history-jump";

export function send(
  command: EditorDispatchCommand,
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
  if (command === "aqe:chorusing-practice") {
    toggleChorusingForOrd(ord);
    return;
  }
  if (command === "aqe:chorusing-next") {
    moveChorusingForOrd(ord, "next");
    return;
  }
  if (command === "aqe:chorusing-previous") {
    moveChorusingForOrd(ord, "previous");
    return;
  }
  if (command === "aqe:play" && pauseChorusingForNormalPlay(ord)) {
    return;
  }
  if (command === "aqe:play" && handleHtmlPlaybackCommand(ord)) {
    return;
  }
  if (command === "aqe:play-recording") {
    toggleLearnerRecordingHtmlPlayback(ord);
    return;
  }
  if (shouldPlayAfterSuccessfulEdit(command)) {
    rememberPostEditPlaybackIntent(ord);
  }
  if (command !== "aqe:history-jump" && BUSY_COMMANDS.has(command)) {
    stopAllEditorPlayback();
    setControlsBusy(ord, true, processingMessage(command, payload, editorRuntimeConfig()));
  }
  const effectivePayload =
    payload ??
    (command === "aqe:pitch-hum" || command === "aqe:share" || command === "aqe:share-recording"
      ? buildSplitCommandPayload(command, ord)
      : undefined);
  if (effectivePayload) {
    focusAndSendCommandPayload(ord, effectivePayload);
    return;
  }
  if (command === "aqe:history-jump") return;
  focusAndSendCommand(ord, command);
}

function shouldPlayAfterSuccessfulEdit(command: EditorDispatchCommand): boolean {
  return (
    command === "aqe:history-jump"
    || command === "aqe:undo"
    || command === "aqe:redo"
    || PROCESSING_COMMANDS.has(command)
  );
}

function stopAllEditorPlayback(): void {
  for (const editorVisualizer of allVisualizers()) {
    if (playbackStateFor(editorVisualizer) === "stopped") continue;
    stopProgressClock(editorVisualizer);
    focusAndSendCommand(Number(editorVisualizer.dataset.aqeFieldOrd || "0"), "aqe:stop-playback");
  }
}
