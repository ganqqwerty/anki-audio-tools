import {
  formatDpdfnetAggressiveness,
  formatOutputFormat,
  outputFormatOrDefault,
} from "./audio-operation-parameters.js";
import { t } from "./i18n.js";
import type { CommandIconName } from "./icon-types.js";
import { EditorButtonMode } from "./types.js";

export type EditorCommand =
  | "aqe:play"
  | "aqe:analyze"
  | "aqe:record-voice"
  | "aqe:play-recording"
  | "aqe:show-file"
  | "aqe:share"
  | "aqe:convert"
  | "aqe:delete-selection"
  | "aqe:delete-rest"
  | "aqe:remove-pauses"
  | "aqe:denoise-standard"
  | "aqe:rnnoise"
  | "aqe:dpdfnet"
  | "aqe:voice-only"
  | "aqe:pitch-hum"
  | "aqe:slower"
  | "aqe:faster"
  | "aqe:volume-down"
  | "aqe:volume-up"
  | "aqe:undo"
  | "aqe:redo"
  | "aqe:settings";

export type EditorButtonDisplayMode = EditorButtonMode;
export type EditorButtonModes = Partial<Record<EditorCommand, EditorButtonDisplayMode>>;

export interface ToolbarButtonSpec {
  activeIcon?: CommandIconName;
  command: EditorCommand;
  icon: CommandIconName;
  iconOnly?: boolean;
  label: string;
  title: string;
}

export const DEFAULT_VISIBLE_EDITOR_BUTTONS = [
  "aqe:play",
  "aqe:analyze",
  "aqe:record-voice",
  "aqe:play-recording",
  "aqe:show-file",
  "aqe:share",
  "aqe:convert",
  "aqe:remove-pauses",
  "aqe:denoise-standard",
  "aqe:pitch-hum",
  "aqe:slower",
  "aqe:faster",
  "aqe:volume-down",
  "aqe:volume-up",
  "aqe:undo",
  "aqe:redo",
  "aqe:settings",
] as const satisfies readonly EditorCommand[];

export const DEFAULT_EDITOR_BUTTON_MODES = {
  "aqe:play": EditorButtonMode.Text,
  "aqe:analyze": EditorButtonMode.Text,
  "aqe:record-voice": EditorButtonMode.Text,
  "aqe:play-recording": EditorButtonMode.Text,
  "aqe:show-file": EditorButtonMode.Text,
  "aqe:share": EditorButtonMode.Text,
  "aqe:convert": EditorButtonMode.Text,
  "aqe:remove-pauses": EditorButtonMode.Text,
  "aqe:denoise-standard": EditorButtonMode.Text,
  "aqe:pitch-hum": EditorButtonMode.Text,
  "aqe:slower": EditorButtonMode.Text,
  "aqe:faster": EditorButtonMode.Text,
  "aqe:volume-down": EditorButtonMode.Text,
  "aqe:volume-up": EditorButtonMode.Text,
  "aqe:undo": EditorButtonMode.Text,
  "aqe:redo": EditorButtonMode.Text,
  "aqe:settings": EditorButtonMode.Text,
} as const satisfies Record<(typeof DEFAULT_VISIBLE_EDITOR_BUTTONS)[number], EditorButtonDisplayMode>;

const DEFAULT_VISIBLE_EDITOR_BUTTON_SET = new Set<EditorCommand>(DEFAULT_VISIBLE_EDITOR_BUTTONS);

function formatDenoiseAlgorithm(value: "standard" | "rnnoise" | "dpdfnet" | "voice_only"): string {
  if (value === "rnnoise") return t("settings.denoise_algorithm.rnnoise");
  if (value === "dpdfnet") return t("settings.denoise_algorithm.dpdfnet");
  if (value === "voice_only") return t("settings.denoise_algorithm.voice_only");
  return t("settings.denoise_algorithm.standard");
}

export function commandButtons(): readonly ToolbarButtonSpec[] {
  const outputFormat = outputFormatOrDefault(
    window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.outputFormat,
  );
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
      command: "aqe:record-voice",
      icon: "mic",
      label: t("editor.command.record_voice.label"),
      title: t("editor.command.record_voice.title"),
    },
    {
      command: "aqe:play-recording",
      icon: "play",
      label: t("editor.command.play_recording.label"),
      title: t("editor.command.play_recording.title"),
    },
    {
      command: "aqe:show-file",
      icon: "folder-open",
      iconOnly: true,
      label: t("editor.command.folder.label"),
      title: t("editor.command.folder.title"),
    },
    {
      command: "aqe:share",
      icon: "share-2",
      iconOnly: true,
      label: t("editor.command.share.label"),
      title: t("editor.command.share.title"),
    },
    {
      command: "aqe:convert",
      icon: "file-audio",
      iconOnly: true,
      label: t("editor.command.convert.label"),
      title: t("editor.command.convert.title", { format: formatOutputFormat(outputFormat) }),
    },
    {
      command: "aqe:remove-pauses",
      icon: "timer-reset",
      iconOnly: true,
      label: t("editor.command.shorten_pauses.label"),
      title: t("editor.command.shorten_pauses.title"),
    },
    {
      command: "aqe:pitch-hum",
      icon: "waves",
      iconOnly: true,
      label: t("editor.command.pitch_hum.label"),
      title: t("editor.command.pitch_hum.title"),
    },
    {
      command: "aqe:slower",
      icon: "snail",
      iconOnly: true,
      label: t("editor.command.slower.label"),
      title: t("editor.command.slower.title"),
    },
    {
      command: "aqe:faster",
      icon: "hare-running",
      iconOnly: true,
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

export function denoiseTopLevelButton(): ToolbarButtonSpec {
  return {
    command: "aqe:denoise-standard",
    icon: "sparkles",
    iconOnly: true,
    label: t("editor.command.denoise.label"),
    title: t("editor.command.denoise.title", {
      algorithm: formatDenoiseAlgorithm("standard"),
    }),
  };
}

export function toolbarButtons(): readonly ToolbarButtonSpec[] {
  return commandButtons().flatMap((button) =>
    button.command === "aqe:remove-pauses" ? [button, denoiseTopLevelButton()] : [button],
  );
}

export function visibleToolbarButtons(
  buttons: readonly ToolbarButtonSpec[],
  visibleCommands: readonly EditorCommand[] | undefined,
): readonly ToolbarButtonSpec[] {
  if (!Array.isArray(visibleCommands)) return buttons;
  const requested = new Set(
    visibleCommands.filter((command): command is EditorCommand =>
      DEFAULT_VISIBLE_EDITOR_BUTTON_SET.has(command),
    ),
  );
  return buttons.filter((button) => requested.has(button.command));
}

export function buttonDisplayMode(
  command: EditorCommand,
  modes: EditorButtonModes | undefined,
): EditorButtonDisplayMode {
  const configuredMode = modes?.[command];
  if (configuredMode === EditorButtonMode.Icon) return EditorButtonMode.Icon;
  return (
    DEFAULT_EDITOR_BUTTON_MODES[command as keyof typeof DEFAULT_EDITOR_BUTTON_MODES] ??
    EditorButtonMode.Text
  );
}

export function denoiseButtons(): readonly ToolbarButtonSpec[] {
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

export const COMMAND_SLUGS: Readonly<Record<EditorCommand, string>> = {
  "aqe:play": "play",
  "aqe:analyze": "graph",
  "aqe:record-voice": "record-voice",
  "aqe:play-recording": "play-recording",
  "aqe:show-file": "show-file",
  "aqe:share": "share",
  "aqe:convert": "convert",
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
