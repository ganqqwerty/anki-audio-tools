import { t } from "../lib/i18n.js";
import type { EditorCommand } from "../lib/editor-toolbar-buttons.js";

export {
  COMMAND_SLUGS,
  DEFAULT_VISIBLE_EDITOR_BUTTONS,
  commandButtons,
  denoiseButtons,
  denoiseTopLevelButton,
  testId,
  toolbarButtons,
  visibleToolbarButtons,
} from "../lib/editor-toolbar-buttons.js";

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
  "aqe:pitch-hum",
  "aqe:volume-down",
  "aqe:volume-up",
]);

export function processingMessage(command: EditorCommand): string {
  if (command === "aqe:denoise-standard") return `${t("editor.status.denoising_standard")}...`;
  if (command === "aqe:rnnoise") return `${t("editor.status.denoising_rnnoise")}...`;
  if (command === "aqe:dpdfnet") return `${t("editor.status.denoising_dpdfnet")}...`;
  if (command === "aqe:voice-only") return `${t("editor.status.extracting_voice")}...`;
  if (command === "aqe:pitch-hum") return `${t("editor.status.pitch_hum")}...`;
  if (command === "aqe:delete-selection") return t("editor.status.deleting_region");
  if (command === "aqe:delete-rest") return t("editor.status.deleting_rest");
  return t("editor.status.processing");
}
