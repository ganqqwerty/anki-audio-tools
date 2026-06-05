import {
  formatDpdfnetAggressiveness,
  formatOutputFormat,
  outputFormatOrDefault,
} from "./audio-operation-parameters.js";
import { t } from "./i18n.js";
import { formatSizeReductionMode, sizeReductionModeOrDefault } from "./size-reduction-parameters.js";
import type { CommandIconName } from "./icon-types.js";
import { EditorButtonMode } from "./types.js";

export type EditorCommand =
  | "aqe:play"
  | "aqe:analyze"
  | "aqe:chorusing-practice"
  | "aqe:chorusing-previous"
  | "aqe:chorusing-next"
  | "aqe:record-voice"
  | "aqe:stop-recording"
  | "aqe:play-recording"
  | "aqe:share-recording"
  | "aqe:show-recording-file"
  | "aqe:show-file"
  | "aqe:share"
  | "aqe:convert"
  | "aqe:reduce-size"
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
  "aqe:chorusing-practice",
  "aqe:chorusing-previous",
  "aqe:chorusing-next",
  "aqe:show-file",
  "aqe:share",
  "aqe:reduce-size",
  "aqe:remove-pauses",
  "aqe:denoise-standard",
  "aqe:slower",
  "aqe:faster",
  "aqe:delete-selection",
  "aqe:delete-rest",
  "aqe:undo",
  "aqe:redo",
  "aqe:settings",
] as const satisfies readonly EditorCommand[];

export const DEFAULT_EDITOR_BUTTON_MODES = {
  "aqe:play": EditorButtonMode.Icon,
  "aqe:analyze": EditorButtonMode.Icon,
  "aqe:chorusing-practice": EditorButtonMode.Icon,
  "aqe:chorusing-previous": EditorButtonMode.Icon,
  "aqe:chorusing-next": EditorButtonMode.Icon,
  "aqe:record-voice": EditorButtonMode.Icon,
  "aqe:play-recording": EditorButtonMode.Icon,
  "aqe:share-recording": EditorButtonMode.Icon,
  "aqe:show-recording-file": EditorButtonMode.Icon,
  "aqe:show-file": EditorButtonMode.Icon,
  "aqe:share": EditorButtonMode.Icon,
  "aqe:convert": EditorButtonMode.Text,
  "aqe:reduce-size": EditorButtonMode.Text,
  "aqe:remove-pauses": EditorButtonMode.Text,
  "aqe:denoise-standard": EditorButtonMode.Text,
  "aqe:pitch-hum": EditorButtonMode.Text,
  "aqe:slower": EditorButtonMode.Icon,
  "aqe:faster": EditorButtonMode.Icon,
  "aqe:volume-down": EditorButtonMode.Icon,
  "aqe:volume-up": EditorButtonMode.Icon,
  "aqe:delete-selection": EditorButtonMode.Icon,
  "aqe:delete-rest": EditorButtonMode.Icon,
  "aqe:undo": EditorButtonMode.Icon,
  "aqe:redo": EditorButtonMode.Icon,
  "aqe:settings": EditorButtonMode.Icon,
} as const satisfies EditorButtonModes;

function formatDenoiseAlgorithm(value: "standard" | "rnnoise" | "dpdfnet" | "voice_only"): string {
  if (value === "rnnoise") return t("settings.denoise_algorithm.rnnoise");
  if (value === "dpdfnet") return t("settings.denoise_algorithm.dpdfnet");
  if (value === "voice_only") return t("settings.denoise_algorithm.voice_only");
  return t("settings.denoise_algorithm.standard");
}

export function commandButtons(): readonly ToolbarButtonSpec[] {
  const outputFormat = outputFormatOrDefault(window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.outputFormat);
  const sizeReductionMode = sizeReductionModeOrDefault(window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.sizeReductionMode);
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
      activeIcon: "chart-line",
      command: "aqe:analyze",
      icon: "chart-line",
      iconOnly: true,
      label: t("editor.command.graph.label"),
      title: t("editor.command.graph.title"),
    },
    {
      activeIcon: "pause",
      command: "aqe:chorusing-practice",
      icon: "bug-play",
      iconOnly: true,
      label: t("editor.command.chorusing_practice.label"),
      title: t("editor.command.chorusing_practice.title"),
    },
    {
      command: "aqe:chorusing-next",
      icon: "skip-back",
      iconOnly: true,
      label: t("editor.command.chorusing_next.label"),
      title: t("editor.command.chorusing_next.title"),
    },
    {
      command: "aqe:chorusing-previous",
      icon: "skip-forward",
      iconOnly: true,
      label: t("editor.command.chorusing_previous.label"),
      title: t("editor.command.chorusing_previous.title"),
    },
    {
      activeIcon: "square",
      command: "aqe:record-voice",
      icon: "mic",
      iconOnly: true,
      label: t("editor.command.record_voice.label"),
      title: t("editor.command.record_voice.title"),
    },
    {
      activeIcon: "pause",
      command: "aqe:play-recording",
      icon: "audio-lines",
      iconOnly: true,
      label: t("editor.command.play_recording.label"),
      title: t("editor.command.play_recording.title"),
    },
    {
      command: "aqe:share-recording",
      icon: "share",
      iconOnly: true,
      label: t("editor.command.share_recording.label"),
      title: t("editor.command.share_recording.title"),
    },
    {
      command: "aqe:show-recording-file",
      icon: "folder-open",
      iconOnly: true,
      label: t("editor.command.show_recording_file.label"),
      title: t("editor.command.show_recording_file.title"),
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
      icon: "share",
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
      command: "aqe:reduce-size",
      icon: "minimize-2",
      iconOnly: true,
      label: t("editor.command.reduce_size.label"),
      title: t("editor.command.reduce_size.title", { level: formatSizeReductionMode(sizeReductionMode) }),
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

export function buttonDisplayMode(
  command: EditorCommand,
  modes: EditorButtonModes | undefined,
): EditorButtonDisplayMode {
  const configuredMode = modes?.[command];
  if (configuredMode === EditorButtonMode.Icon) return EditorButtonMode.Icon;
  if (configuredMode === EditorButtonMode.Text) return EditorButtonMode.Text;
  return DEFAULT_EDITOR_BUTTON_MODES[command as keyof typeof DEFAULT_EDITOR_BUTTON_MODES] ?? EditorButtonMode.Text;
}

export function denoiseButtons(): readonly ToolbarButtonSpec[] {
  const dpdfnetAttnLimitDb = window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.dpdfnetAttnLimitDb ?? 12;
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
