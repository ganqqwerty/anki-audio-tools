import { BUSY_COMMANDS, PROCESSING_COMMANDS, processingMessage } from "./commands.js";
import { focusAndSendCommand, focusAndSendCommandPayload } from "./bridge.js";
import { quiesceTransportBeforeEditorMutation } from "./editor-command-coordinator.js";
import { logger } from "./logger.js";
import { requestGraph } from "./graph-actions.js";
import { buildSplitCommandPayload } from "./split-button-state.js";
import { rememberPostEditPlaybackIntent } from "./post-edit-playback.js";
import {
  handleHtmlPlaybackCommand,
} from "./playback-actions.js";
import { moveChorusingForOrd } from "./chorusing-controller.js";
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
  if (command === "aqe:chorusing-next") {
    moveChorusingForOrd(ord, "next");
    return;
  }
  if (command === "aqe:chorusing-previous") {
    moveChorusingForOrd(ord, "previous");
    return;
  }
  if (command === "aqe:play" && handleHtmlPlaybackCommand(ord)) {
    return;
  }
  if (command === "aqe:play-recording") {
    toggleLearnerRecordingHtmlPlayback(ord);
    return;
  }
  const postEditAutoplay = shouldPlayAfterSuccessfulEdit(command)
    ? rememberPostEditPlaybackIntent(ord)
    : null;
  if (command !== "aqe:history-jump" && BUSY_COMMANDS.has(command)) {
    stopAllEditorPlayback();
    setControlsBusy(ord, true, processingMessage(command, payload, editorRuntimeConfig()));
  }
  let effectivePayload =
    payload ??
    (command === "aqe:pitch-hum" || command === "aqe:share" || command === "aqe:share-recording"
      ? buildSplitCommandPayload(command, ord)
      : undefined);
  if (postEditAutoplay) {
    effectivePayload = {
      ...(effectivePayload ?? { command }),
      command: effectivePayload?.command ?? command,
      fieldOrd: effectivePayload?.fieldOrd ?? ord,
      postEditAutoplay,
    };
  }
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
  quiesceTransportBeforeEditorMutation();
}
