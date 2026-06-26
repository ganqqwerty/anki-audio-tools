import { AudioExportMode } from "$lib/types.js";
import type {
  AudioExportFieldSelection,
  AudioExportInitialState,
  AudioExportStartRequest,
} from "$lib/types.js";

export interface AudioExportFormState {
  mode: AudioExportMode;
  destinationPath: string;
  selectedFields: Record<string, Set<string>>;
  silenceBetweenClipsSeconds: number;
  normalizeVolume: boolean;
}

export function initialAudioExportFormState(state: AudioExportInitialState): AudioExportFormState {
  const defaults = new Map(
    state.default_field_selections.map((selection) => [selection.notetype_name, selection.fields]),
  );
  const selectedFields: Record<string, Set<string>> = {};
  for (const group of state.field_groups) {
    selectedFields[group.notetype_name] = new Set(defaults.get(group.notetype_name) ?? []);
  }
  return {
    mode: state.defaults.mode,
    destinationPath: "",
    selectedFields,
    silenceBetweenClipsSeconds: clampSilenceSeconds(state.defaults.silence_between_clips_seconds),
    normalizeVolume: state.defaults.normalize_volume,
  };
}

export function canStartAudioExport(form: AudioExportFormState): boolean {
  return form.destinationPath.trim().length > 0 && selectedFieldCount(form) > 0;
}

export function audioExportStartRequest(form: AudioExportFormState): AudioExportStartRequest {
  return {
    mode: form.mode,
    destination_path: form.destinationPath.trim(),
    field_selections: audioExportFieldSelections(form),
    silence_between_clips_seconds: clampSilenceSeconds(form.silenceBetweenClipsSeconds),
    normalize_volume: form.normalizeVolume,
  };
}

export function setAudioExportFieldSelected(
  form: AudioExportFormState,
  notetypeName: string,
  field: string,
  selected: boolean,
): void {
  const fields = new Set(form.selectedFields[notetypeName] ?? []);
  if (selected) {
    fields.add(field);
  } else {
    fields.delete(field);
  }
  form.selectedFields = {
    ...form.selectedFields,
    [notetypeName]: fields,
  };
}

export function selectedFieldCount(form: AudioExportFormState): number {
  return Object.values(form.selectedFields).reduce((total, fields) => total + fields.size, 0);
}

export function clampSilenceSeconds(value: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.min(10, Math.max(0, value));
}

function audioExportFieldSelections(form: AudioExportFormState): AudioExportFieldSelection[] {
  return Object.entries(form.selectedFields)
    .map(([notetypeName, fields]) => ({
      notetype_name: notetypeName,
      fields: [...fields],
    }))
    .filter((selection) => selection.fields.length > 0);
}
