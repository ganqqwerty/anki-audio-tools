import {
  formatOutputFormat,
  outputFormatOrDefault,
} from "../lib/audio-operation-parameters.js";
import { t } from "../lib/i18n.js";
import { formatSizeReductionMode, sizeReductionModeOrDefault } from "../lib/size-reduction-parameters.js";
import type { EditorCommand, EditorCommandPayload } from "./types.js";

export {
  DEFAULT_VISIBLE_EDITOR_BUTTONS,
  commandButtons,
  denoiseButtons,
  denoiseTopLevelButton,
  toolbarButtons,
} from "../lib/editor-toolbar-buttons.js";
export { COMMAND_SLUGS, testId } from "../lib/editor-toolbar-command-slugs.js";
export { visibleToolbarButtons } from "../lib/editor-toolbar-visibility.js";

export const PROCESSING_COMMANDS = new Set<EditorCommand>([
  "aqe:slower",
  "aqe:faster",
  "aqe:convert",
  "aqe:reduce-size",
  "aqe:remove-pauses",
  "aqe:denoise-standard",
  "aqe:rnnoise",
  "aqe:dpdfnet",
  "aqe:voice-only",
  "aqe:pitch-hum",
  "aqe:volume-down",
  "aqe:volume-up",
]);

export const BUSY_COMMANDS = new Set<EditorCommand>([
  ...PROCESSING_COMMANDS,
  "aqe:share",
  "aqe:share-recording",
]);

export interface ProcessingMessageConfig {
  splitButtonDefaults?: {
    outputFormat?: unknown;
    sizeReductionMode?: unknown;
  };
}

export function processingMessage(command: EditorCommand, payload?: EditorCommandPayload, config: ProcessingMessageConfig = {}): string {
  if (command === "aqe:denoise-standard") return `${t("editor.status.denoising_standard")}...`;
  if (command === "aqe:rnnoise") return `${t("editor.status.denoising_rnnoise")}...`;
  if (command === "aqe:dpdfnet") return `${t("editor.status.denoising_dpdfnet")}...`;
  if (command === "aqe:voice-only") return `${t("editor.status.extracting_voice")}...`;
  if (command === "aqe:pitch-hum") return `${t("editor.status.pitch_hum")}...`;
  if (command === "aqe:share" || command === "aqe:share-recording") {
    const shareTarget = payload?.shareTarget ?? "litterbox";
    return shareTarget === "litterbox"
      ? `${t("editor.status.sharing_litterbox")}...`
      : `${t("editor.status.sharing_catbox")}...`;
  }
  if (command === "aqe:convert") {
    const outputFormat = outputFormatOrDefault(
      payload?.overrides?.targetFormat ??
        config.splitButtonDefaults?.outputFormat,
    );
    return `${t("editor.status.converting", { format: formatOutputFormat(outputFormat) })}...`;
  }
  if (command === "aqe:reduce-size") {
    const mode = sizeReductionModeOrDefault(
      payload?.overrides?.sizeReductionMode ??
        config.splitButtonDefaults?.sizeReductionMode,
    );
    return `${t("editor.status.reducing_size_with_level", { level: formatSizeReductionMode(mode) })}...`;
  }
  if (command === "aqe:delete-selection") return t("editor.status.deleting_region");
  if (command === "aqe:delete-rest") return t("editor.status.deleting_rest");
  return t("editor.status.processing");
}
