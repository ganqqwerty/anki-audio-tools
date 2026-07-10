import type { EditorCommand } from "./editor-toolbar-buttons.js";

export const COMMAND_SLUGS: Readonly<Record<EditorCommand, string>> = {
  "aqe:play": "play",
  "aqe:analyze": "graph",
  "aqe:chorusing-previous": "chorusing-previous",
  "aqe:chorusing-next": "chorusing-next",
  "aqe:record-voice": "record-voice",
  "aqe:stop-recording": "stop-recording",
  "aqe:play-recording": "play-recording",
  "aqe:share-recording": "share-recording",
  "aqe:show-recording-file": "show-recording-file",
  "aqe:show-file": "show-file",
  "aqe:share": "share",
  "aqe:preset": "preset",
  "aqe:convert": "convert",
  "aqe:reduce-size": "reduce-size",
  "aqe:delete-selection": "delete-selection",
  "aqe:delete-rest": "delete-rest",
  "aqe:remove-pauses": "remove-pauses",
  "aqe:denoise-standard": "denoise-standard",
  "aqe:rnnoise": "rnnoise",
  "aqe:dpdfnet": "dpdfnet",
  "aqe:voice-only": "voice-only",
  "aqe:pitch-hum": "pitch-hum",
  "aqe:slower": "slower",
  "aqe:faster": "faster",
  "aqe:volume-down": "volume-down",
  "aqe:volume-up": "volume-up",
  "aqe:undo": "undo",
  "aqe:redo": "redo",
  "aqe:settings": "settings",
};

export function testId(ord: number, command: EditorCommand): string {
  return `aqe-button-${ord}-${COMMAND_SLUGS[command]}`;
}
