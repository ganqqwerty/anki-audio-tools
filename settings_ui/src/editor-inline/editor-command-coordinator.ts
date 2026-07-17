import { stopAndQuiesceHtmlAudioTransport } from "./html-audio-session-controller.js";
import { cancelEditorPracticeProgram } from "./editor-practice-controller.js";

/** Stops the authoritative transport before an editor command can mutate its source. */
export function quiesceTransportBeforeEditorMutation(): number | null {
  cancelEditorPracticeProgram();
  return stopAndQuiesceHtmlAudioTransport();
}
