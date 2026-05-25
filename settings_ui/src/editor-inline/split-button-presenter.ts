import { t } from "../lib/i18n.js";
import { formatGraphRecordingCondition, formatGraphSmoothness, formatGraphVoiceLock, formatGraphVoiceRange } from "./graph-split-values.js";
import {
  formatDenoiseAlgorithm,
  formatOutputFormat,
  formatSpeedStep,
  formatVoiceRecordingCountdownSeconds,
  formatVolumeDb,
} from "./split-button-state.js";
import type { GraphRecordingCondition, GraphSmoothness, GraphVoiceLock, GraphVoiceRange } from "./graph-settings.js";
import type { ButtonSpec, FieldSplitButtonState } from "./types.js";

type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
type OutputFormatValue = FieldSplitButtonState["outputFormat"];
type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
type ShareTarget = FieldSplitButtonState["shareTarget"];

type SplitButtonValueState = {
  denoiseAlgorithm: DenoiseAlgorithm;
  dpdfnetAttnLimitDb: number;
  graphConnectShortDropoutsMs: number;
  graphRecordingCondition: GraphRecordingCondition;
  graphSmoothness: GraphSmoothness;
  graphVoiceLock: GraphVoiceLock;
  graphVoiceRange: GraphVoiceRange;
  outputFormat: OutputFormatValue;
  pauseAggressiveness: FieldSplitButtonState["pauseAggressiveness"];
  pitchHumMode: PitchHumMode;
  shareTarget: ShareTarget;
  speedStep: number;
  voiceRecordingCountdownSeconds: number;
  volumeStepDb: number;
};

export function graphSummary(state: SplitButtonValueState): string {
  return [
    formatGraphVoiceRange(state.graphVoiceRange),
    formatGraphRecordingCondition(state.graphRecordingCondition),
    formatGraphSmoothness(state.graphSmoothness),
    `${state.graphConnectShortDropoutsMs} ms`,
    formatGraphVoiceLock(state.graphVoiceLock),
  ].join(" · ");
}

export function isDenoiseCommand(command: ButtonSpec["command"]): boolean {
  return (
    command === "aqe:denoise-standard" ||
    command === "aqe:rnnoise" ||
    command === "aqe:dpdfnet" ||
    command === "aqe:voice-only"
  );
}

export function primaryTitle(
  button: ButtonSpec,
  outputFormat: OutputFormatValue,
  denoiseAlgorithm: DenoiseAlgorithm,
): string {
  if (button.command === "aqe:convert") {
    return t("editor.command.convert.title", { format: formatOutputFormat(outputFormat) });
  }
  if (!isDenoiseCommand(button.command)) return button.title;
  return t("editor.command.denoise.title", { algorithm: formatDenoiseAlgorithm(denoiseAlgorithm) });
}

function groupedSpeedValueLabel(speedStep: number): string {
  return formatSpeedStep(speedStep, "aqe:faster");
}

function denoiseValueLabel(denoiseAlgorithm: DenoiseAlgorithm, dpdfnetAttnLimitDb: number): string {
  if (denoiseAlgorithm !== "dpdfnet") {
    return formatDenoiseAlgorithm(denoiseAlgorithm);
  }
  const aggressivenessKey =
    dpdfnetAttnLimitDb === 6 ? "gentle" : dpdfnetAttnLimitDb === 18 ? "aggressive" : "normal";
  return `${formatDenoiseAlgorithm(denoiseAlgorithm)} (${t(`settings.pause_aggressiveness.${aggressivenessKey}`)})`;
}

export function currentValueLabel(
  button: ButtonSpec,
  groupSlug: "speed" | "volume" | undefined,
  state: SplitButtonValueState,
): string {
  if (groupSlug === "volume") return formatVolumeDb(state.volumeStepDb);
  if (groupSlug === "speed") return groupedSpeedValueLabel(state.speedStep);
  if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") return formatVolumeDb(state.volumeStepDb);
  if (button.command === "aqe:faster" || button.command === "aqe:slower") return formatSpeedStep(state.speedStep, button.command);
  if (button.command === "aqe:remove-pauses") {
    return state.pauseAggressiveness === "aggressive"
      ? t("settings.pause_aggressiveness.aggressive")
      : state.pauseAggressiveness === "gentle"
        ? t("settings.pause_aggressiveness.gentle")
        : t("settings.pause_aggressiveness.normal");
  }
  if (button.command === "aqe:convert") return formatOutputFormat(state.outputFormat);
  if (button.command === "aqe:share") {
    return state.shareTarget === "litterbox" ? t("editor.share.target.litterbox") : t("editor.share.target.catbox");
  }
  if (button.command === "aqe:pitch-hum") {
    return state.pitchHumMode === "pitch_tier" ? t("editor.pitch_hum.mode.pitch_tier") : t("editor.pitch_hum.mode.direct");
  }
  if (isDenoiseCommand(button.command)) {
    return denoiseValueLabel(state.denoiseAlgorithm, state.dpdfnetAttnLimitDb);
  }
  if (button.command === "aqe:analyze") return graphSummary(state);
  if (button.command === "aqe:record-voice") {
    return formatVoiceRecordingCountdownSeconds(state.voiceRecordingCountdownSeconds);
  }
  return "";
}
