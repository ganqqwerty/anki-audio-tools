import { t } from "../lib/i18n.js";
import type { FieldSplitButtonState } from "./types.js";

type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
type ShareTarget = FieldSplitButtonState["shareTarget"];

export function formatDenoiseAlgorithm(value: FieldSplitButtonState["denoiseAlgorithm"]): string {
  if (value === "rnnoise") return t("settings.denoise_algorithm.rnnoise");
  if (value === "dpdfnet") return t("settings.denoise_algorithm.dpdfnet");
  if (value === "voice_only") return t("settings.denoise_algorithm.voice_only");
  return t("settings.denoise_algorithm.standard");
}

export function formatPitchHumMode(value: PitchHumMode): string {
  if (value === "pitch_tier") return t("editor.pitch_hum.mode.pitch_tier");
  return t("editor.pitch_hum.mode.direct");
}

export function formatShareTarget(value: ShareTarget): string {
  return value === "litterbox" ? t("editor.share.target.litterbox") : t("editor.share.target.catbox");
}

export function formatPauseDetectionAlgorithm(value: FieldSplitButtonState["pauseDetectionAlgorithm"]): string {
  if (value === "silero_vad") return t("settings.pause_detection_algorithm.silero_vad");
  return t("settings.pause_detection_algorithm.silencedetect");
}
