import { t } from "$lib/i18n.js";
import type { BatchOperationOption } from "$lib/types.js";
import type { BatchFormState } from "./batch-state.js";
import type { AudioExportFormState } from "./export-state.js";
import { selectedFieldCount } from "./export-state.js";

export function batchStartDisabledReason({
  canStart,
  exportForm,
  finished,
  form,
  isAudioExportSurface,
  running,
  selected,
}: {
  canStart: boolean;
  exportForm: AudioExportFormState | null;
  finished: boolean;
  form: BatchFormState;
  isAudioExportSurface: boolean;
  running: boolean;
  selected: BatchOperationOption | undefined;
}): string | undefined {
  if (running) return t("tooltip.disabled.batch_running");
  if (finished) return t("tooltip.disabled.finished");
  if (isAudioExportSurface) {
    if (exportForm === null) return t("tooltip.disabled.audio_export_unavailable");
    if (exportForm.destinationPath.trim().length === 0) return t("tooltip.disabled.audio_export_destination");
    if (selectedFieldCount(exportForm) === 0) return t("tooltip.disabled.audio_export_fields");
    return undefined;
  }
  if (selected === undefined) return t("tooltip.disabled.batch_operation");
  if (form.sourceField.length === 0) return t("tooltip.disabled.batch_source_field");
  if (!canStart) return t("tooltip.disabled.batch_required_fields");
  return undefined;
}
