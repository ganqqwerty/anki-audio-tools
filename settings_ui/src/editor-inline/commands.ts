import type { ButtonSpec, EditorCommand } from "./types.js";

export const COMMAND_BUTTONS: readonly ButtonSpec[] = [
  { activeIcon: "pause", command: "aqe:play", icon: "play", label: "Play", title: "Play or pause current audio" },
  {
    activeIcon: "refresh-cw",
    command: "aqe:analyze",
    icon: "chart-line",
    label: "Graph",
    title: "Analyze and show pitch/intensity graph",
  },
  { command: "aqe:show-file", icon: "folder-open", label: "Folder", title: "Show current audio file in folder" },
  { command: "aqe:trim-left", icon: "scissors", label: "-L", title: "Trim 100 ms from left" },
  { command: "aqe:trim-right", icon: "scissors", label: "-R", title: "Trim 100 ms from right" },
  { command: "aqe:remove-pauses", icon: "timer-reset", label: "Shorten Pauses", title: "Speed up long internal pauses" },
  { command: "aqe:sidon", icon: "wand-sparkles", label: "Sidon", title: "Restore speech with Sidon" },
  { command: "aqe:mp-senet", icon: "sparkles", label: "MP-SENet", title: "Denoise speech with MP-SENet" },
  {
    command: "aqe:remove-noise",
    icon: "volume-x",
    label: "Remove noise",
    title: "Reduce background noise with DeepFilterNet",
  },
  { command: "aqe:slower", icon: "rewind", label: "Slower", title: "Decrease speed" },
  { command: "aqe:faster", icon: "fast-forward", label: "Faster", title: "Increase speed" },
  { command: "aqe:volume-down", icon: "volume-1", label: "Volume -", title: "Decrease volume" },
  { command: "aqe:volume-up", icon: "volume-2", label: "Volume +", title: "Increase volume" },
  { command: "aqe:undo", icon: "undo-2", label: "Undo", title: "Restore the previous generated audio reference" },
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
