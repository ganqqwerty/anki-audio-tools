import type { ButtonSpec, EditorCommand } from "./types.js";

export const COMMAND_BUTTONS: readonly ButtonSpec[] = [
  { command: "aqe:play", label: "Play", title: "Play or pause current audio" },
  { command: "aqe:analyze", label: "Graph", title: "Analyze and show pitch/intensity graph" },
  { command: "aqe:show-file", label: "Folder", title: "Show current audio file in folder" },
  { command: "aqe:trim-left", label: "-L", title: "Trim 100 ms from left" },
  { command: "aqe:trim-right", label: "-R", title: "Trim 100 ms from right" },
  { command: "aqe:remove-pauses", label: "Shorten Pauses", title: "Speed up long internal pauses" },
  { command: "aqe:sidon", label: "Sidon", title: "Restore speech with Sidon" },
  { command: "aqe:mp-senet", label: "MP-SENet", title: "Denoise speech with MP-SENet" },
  {
    command: "aqe:remove-noise",
    label: "Remove noise",
    title: "Reduce background noise with DeepFilterNet",
  },
  { command: "aqe:slower", label: "Slower", title: "Decrease speed" },
  { command: "aqe:faster", label: "Faster", title: "Increase speed" },
  { command: "aqe:volume-down", label: "Volume -", title: "Decrease volume" },
  { command: "aqe:volume-up", label: "Volume +", title: "Increase volume" },
  { command: "aqe:undo", label: "Undo", title: "Restore the previous generated audio reference" },
] as const;

export const PROCESSING_COMMANDS = new Set<EditorCommand>([
  "aqe:trim-left",
  "aqe:trim-right",
  "aqe:slower",
  "aqe:faster",
  "aqe:remove-pauses",
  "aqe:remove-noise",
  "aqe:sidon",
  "aqe:mp-senet",
  "aqe:volume-down",
  "aqe:volume-up",
]);

export const COMMAND_SLUGS: Readonly<Record<EditorCommand, string>> = {
  "aqe:play": "play",
  "aqe:analyze": "graph",
  "aqe:show-file": "show-file",
  "aqe:trim-left": "trim-left",
  "aqe:trim-right": "trim-right",
  "aqe:remove-pauses": "remove-pauses",
  "aqe:remove-noise": "remove-noise",
  "aqe:sidon": "sidon",
  "aqe:mp-senet": "mp-senet",
  "aqe:slower": "slower",
  "aqe:faster": "faster",
  "aqe:volume-down": "volume-down",
  "aqe:volume-up": "volume-up",
  "aqe:undo": "undo",
};

export function testId(ord: number, command: EditorCommand): string {
  return `aqe-button-${ord}-${COMMAND_SLUGS[command]}`;
}

export function processingMessage(command: EditorCommand): string {
  if (command === "aqe:remove-noise") return "Removing noise...";
  if (command === "aqe:sidon") return "Restoring speech...";
  if (command === "aqe:mp-senet") return "Denoising with MP-SENet...";
  return "Processing...";
}
