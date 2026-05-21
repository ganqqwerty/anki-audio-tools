import type { ButtonSpec, EditorCommand } from "./types.js";
import { t } from "../lib/i18n.js";
import { formatDpdfnetAggressiveness } from "../lib/audio-operation-parameters.js";

export function commandButtons(): readonly ButtonSpec[] {
  const trimMs = window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.trimStepMs ?? 100;
  return [
    {
      activeIcon: "pause",
      command: "aqe:play",
      icon: "play",
      iconOnly: true,
      label: t("editor.command.play.label"),
      title: t("editor.command.play.title"),
    },
    {
      activeIcon: "audio-lines",
      command: "aqe:analyze",
      icon: "audio-lines",
      iconOnly: true,
      label: t("editor.command.graph.label"),
      title: t("editor.command.graph.title"),
    },
    {
      command: "aqe:show-file",
      icon: "folder-open",
      label: t("editor.command.folder.label"),
      title: t("editor.command.folder.title"),
    },
    {
      command: "aqe:trim-left",
      icon: "scissors",
      label: t("editor.command.trim_left.label"),
      title: t("editor.command.trim_left.title", { ms: trimMs }),
    },
    {
      command: "aqe:trim-right",
      icon: "scissors",
      label: t("editor.command.trim_right.label"),
      title: t("editor.command.trim_right.title", { ms: trimMs }),
    },
    {
      command: "aqe:remove-pauses",
      icon: "timer-reset",
      label: t("editor.command.shorten_pauses.label"),
      title: t("editor.command.shorten_pauses.title"),
    },
    {
      command: "aqe:slower",
      icon: "snail",
      label: t("editor.command.slower.label"),
      title: t("editor.command.slower.title"),
    },
    {
      command: "aqe:faster",
      icon: "hare-running",
      label: t("editor.command.faster.label"),
      title: t("editor.command.faster.title"),
    },
    {
      command: "aqe:volume-down",
      icon: "volume-1",
      iconOnly: true,
      label: t("editor.command.volume_down.label"),
      title: t("editor.command.volume_down.title"),
    },
    {
      command: "aqe:volume-up",
      icon: "volume-2",
      iconOnly: true,
      label: t("editor.command.volume_up.label"),
      title: t("editor.command.volume_up.title"),
    },
    {
      command: "aqe:undo",
      icon: "undo-2",
      iconOnly: true,
      label: t("editor.command.undo.label"),
      title: t("editor.command.undo.title"),
    },
    {
      command: "aqe:redo",
      icon: "redo-2",
      iconOnly: true,
      label: t("editor.command.redo.label"),
      title: t("editor.command.redo.title"),
    },
    {
      command: "aqe:settings",
      icon: "settings",
      iconOnly: true,
      label: t("editor.command.settings.label"),
      title: t("editor.command.settings.title"),
    },
  ] as const;
}

export function denoiseButtons(): readonly ButtonSpec[] {
  const dpdfnetAttnLimitDb =
    window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.dpdfnetAttnLimitDb ?? 12;
  return [
    {
      command: "aqe:denoise-standard",
      icon: "volume-x",
      label: t("editor.command.standard.label"),
      title: t("editor.command.standard.title"),
    },
    {
      command: "aqe:rnnoise",
      icon: "waves",
      label: t("editor.command.rnnoise.label"),
      title: t("editor.command.rnnoise.title"),
    },
    {
      command: "aqe:dpdfnet",
      icon: "sparkles",
      label: t("editor.command.dpdfnet.label"),
      title: t("editor.command.dpdfnet.title", {
        level: formatDpdfnetAggressiveness(dpdfnetAttnLimitDb),
      }),
    },
    {
      command: "aqe:voice-only",
      icon: "mic",
      label: t("editor.command.voice_only.label"),
      title: t("editor.command.voice_only.title"),
    },
  ] as const;
}

export const PROCESSING_COMMANDS = new Set<EditorCommand>([
  "aqe:trim-left",
  "aqe:trim-right",
  "aqe:slower",
  "aqe:faster",
  "aqe:remove-pauses",
  "aqe:denoise-standard",
  "aqe:rnnoise",
  "aqe:dpdfnet",
  "aqe:voice-only",
  "aqe:volume-down",
  "aqe:volume-up",
]);

export const COMMAND_SLUGS: Readonly<Record<EditorCommand, string>> = {
  "aqe:play": "play",
  "aqe:analyze": "graph",
  "aqe:show-file": "show-file",
  "aqe:delete-selection": "delete-selection",
  "aqe:delete-rest": "delete-rest",
  "aqe:trim-left": "trim-left",
  "aqe:trim-right": "trim-right",
  "aqe:remove-pauses": "remove-pauses",
  "aqe:denoise-standard": "denoise-standard",
  "aqe:rnnoise": "rnnoise",
  "aqe:dpdfnet": "dpdfnet",
  "aqe:voice-only": "voice-only",
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
  if (command === "aqe:denoise-standard") return `${t("editor.status.denoising_standard")}...`;
  if (command === "aqe:rnnoise") return `${t("editor.status.denoising_rnnoise")}...`;
  if (command === "aqe:dpdfnet") return `${t("editor.status.denoising_dpdfnet")}...`;
  if (command === "aqe:voice-only") return `${t("editor.status.extracting_voice")}...`;
  if (command === "aqe:delete-selection") return t("editor.status.deleting_region");
  if (command === "aqe:delete-rest") return t("editor.status.deleting_rest");
  return t("editor.status.processing");
}
