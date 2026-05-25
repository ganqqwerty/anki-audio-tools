import { isOutputFormatValue, OUTPUT_FORMAT_VALUES } from "../lib/audio-operation-parameters.js";
import { t } from "../lib/i18n.js";
import { PRODUCT_LINKS } from "../lib/product-links.js";
import type { EditorCommand } from "../lib/editor-toolbar-buttons.js";
import {
  formatDenoiseAlgorithm,
  formatDpdfnetAggressiveness,
  formatOutputFormat,
  formatPauseAggressiveness,
  formatPitchHumMode,
} from "./split-button-state.js";
import type { FieldSplitButtonState } from "./types.js";

type GroupSlug = "speed" | "volume";
type PitchHumMode = FieldSplitButtonState["pitchHumMode"];

export function splitMenuDescription(
  command: EditorCommand,
  groupSlug: GroupSlug | undefined,
  menuLabel: string,
): string {
  if (groupSlug === "speed") return t("editor.split.description_speed");
  if (groupSlug === "volume") return t("editor.split.description_volume");
  if (command === "aqe:share") return t("editor.split.description_share");
  if (command === "aqe:convert") return t("editor.split.description_convert");
  if (command === "aqe:remove-pauses") return t("editor.split.description_shorten_pauses");
  if (command === "aqe:pitch-hum") return t("editor.split.description_pitch_hum");
  if (isDenoiseCommand(command)) return t("editor.split.description_denoise");
  return t("editor.split.description", { label: menuLabel });
}

export function splitMenuVideoLink(
  command: EditorCommand,
  groupSlug: GroupSlug | undefined,
): string | null {
  if (groupSlug === "speed") return PRODUCT_LINKS.editorVideos.speed;
  if (groupSlug === "volume") return PRODUCT_LINKS.editorVideos.volume;
  if (command === "aqe:share") return PRODUCT_LINKS.editorVideos.share;
  if (command === "aqe:convert") return PRODUCT_LINKS.editorVideos.convert;
  if (command === "aqe:remove-pauses") return PRODUCT_LINKS.editorVideos.pauseShortening;
  if (command === "aqe:pitch-hum") return PRODUCT_LINKS.editorVideos.pitchHum;
  if (isDenoiseCommand(command)) return PRODUCT_LINKS.editorVideos.denoise;
  return null;
}

export function splitOptionValues(command: EditorCommand): string[] {
  if (command === "aqe:remove-pauses") return ["gentle", "normal", "aggressive"];
  if (isDenoiseCommand(command)) return ["standard", "rnnoise", "dpdfnet", "voice_only"];
  if (command === "aqe:convert") return [...OUTPUT_FORMAT_VALUES];
  if (command === "aqe:share") return ["catbox", "litterbox"];
  if (command === "aqe:pitch-hum") return ["direct", "pitch_tier"];
  return [];
}

export function splitOptionLabel(value: string): string {
  if (value === "catbox") return t("editor.share.target.catbox");
  if (value === "litterbox") return t("editor.share.target.litterbox");
  if (isOutputFormatValue(value)) return formatOutputFormat(value);
  if (value === "direct" || value === "pitch_tier") return formatPitchHumMode(value as PitchHumMode);
  if (value === "standard" || value === "rnnoise" || value === "dpdfnet" || value === "voice_only") {
    return formatDenoiseAlgorithm(value);
  }
  if (value === "aggressive" || value === "gentle" || value === "normal") {
    return formatPauseAggressiveness(value);
  }
  return value;
}

export function splitOptionDescription(value: string): string {
  if (isOutputFormatValue(value)) {
    return t(`editor.split.option.output_format.${value}.description`);
  }
  if (value === "aggressive" || value === "gentle" || value === "normal") {
    return t(`editor.split.option.pause.${value}.description`);
  }
  if (value === "direct" || value === "pitch_tier") {
    return t(`editor.split.option.pitch_hum.${value}.description`);
  }
  return "";
}

export function splitOptionTitle(value: string, dpdfnetAttnLimitDb: number): string {
  if (value === "dpdfnet") {
    return t("editor.command.dpdfnet.title", {
      level: formatDpdfnetAggressiveness(dpdfnetAttnLimitDb),
    });
  }
  if (value === "pitch_tier") return t("editor.pitch_hum.mode.pitch_tier.title");
  if (value === "direct") return t("editor.command.pitch_hum.title");
  return splitOptionLabel(value);
}

function isDenoiseCommand(command: EditorCommand): boolean {
  return (
    command === "aqe:denoise-standard" ||
    command === "aqe:rnnoise" ||
    command === "aqe:dpdfnet" ||
    command === "aqe:voice-only"
  );
}
