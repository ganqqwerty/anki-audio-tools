import type { ButtonSpec, EditorCommand } from "./types.js";

export const COMMAND_BUTTONS: readonly ButtonSpec[] = [
  { activeIcon: "pause", command: "aqe:play", icon: "play", iconOnly: true, label: "Play", title: "Play or pause current audio" },
  {
    activeIcon: "audio-lines",
    command: "aqe:analyze",
    icon: "audio-lines",
    iconOnly: true,
    label: "Graph",
    title: "Analyze and show pitch/intensity graph",
  },
  { command: "aqe:show-file", icon: "folder-open", label: "Folder", title: "Show current audio file in folder" },
  { command: "aqe:trim-left", icon: "scissors", label: "-L", title: "Trim 100 ms from left" },
  { command: "aqe:trim-right", icon: "scissors", label: "-R", title: "Trim 100 ms from right" },
  { command: "aqe:remove-pauses", icon: "timer-reset", label: "Shorten Pauses", title: "Speed up long internal pauses" },
  { command: "aqe:slower", icon: "rewind", label: "Slower", title: "Decrease speed" },
  { command: "aqe:faster", icon: "fast-forward", label: "Faster", title: "Increase speed" },
  { command: "aqe:volume-down", icon: "volume-1", iconOnly: true, label: "Volume -", title: "Decrease volume" },
  { command: "aqe:volume-up", icon: "volume-2", iconOnly: true, label: "Volume +", title: "Increase volume" },
  { command: "aqe:undo", icon: "undo-2", iconOnly: true, label: "Undo", title: "Restore the previous generated audio reference" },
  { command: "aqe:redo", icon: "redo-2", iconOnly: true, label: "Redo", title: "Restore the most recently undone audio reference" },
  { command: "aqe:settings", icon: "settings", iconOnly: true, label: "Settings", title: "Open Audio Quick Editor settings" },
] as const;

export const DENOISE_BUTTONS: readonly ButtonSpec[] = [
  {
    command: "aqe:denoise-standard",
    icon: "volume-x",
    label: "Standard",
    title: "Denoise speech with DeepFilterNet",
  },
  { command: "aqe:rnnoise", icon: "waves", label: "RNNoise", title: "Denoise speech with RNNoise" },
] as const;

export const PROCESSING_COMMANDS = new Set<EditorCommand>([
  "aqe:trim-left",
  "aqe:trim-right",
  "aqe:slower",
  "aqe:faster",
  "aqe:remove-pauses",
  "aqe:denoise-standard",
  "aqe:rnnoise",
  "aqe:volume-down",
  "aqe:volume-up",
]);

export const COMMAND_SLUGS: Readonly<Record<EditorCommand, string>> = {
  "aqe:play": "play",
  "aqe:analyze": "graph",
  "aqe:show-file": "show-file",
  "aqe:delete-selection": "delete-selection",
  "aqe:trim-left": "trim-left",
  "aqe:trim-right": "trim-right",
  "aqe:remove-pauses": "remove-pauses",
  "aqe:denoise-standard": "denoise-standard",
  "aqe:rnnoise": "rnnoise",
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

export function processingMessage(command: EditorCommand): string {
  if (command === "aqe:denoise-standard") return "Denoising with Standard...";
  if (command === "aqe:rnnoise") return "Denoising with RNNoise...";
  if (command === "aqe:delete-selection") return "Deleting region...";
  return "Processing...";
}
