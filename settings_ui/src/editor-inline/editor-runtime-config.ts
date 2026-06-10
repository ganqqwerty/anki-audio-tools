import type { EditorRuntimeConfig } from "./types.js";

const FALLBACK_EDITOR_RUNTIME_CONFIG: EditorRuntimeConfig = { audioFieldIndices: [] };

export function editorRuntimeConfig(): EditorRuntimeConfig {
  return window.__AQE_EDITOR_CONFIG__ ?? FALLBACK_EDITOR_RUNTIME_CONFIG;
}

export function splitButtonDefaults(config: EditorRuntimeConfig): NonNullable<EditorRuntimeConfig["splitButtonDefaults"]> {
  return config.splitButtonDefaults ?? {};
}

export function repeatPlaybackByDefault(config: EditorRuntimeConfig): boolean {
  return config.repeatPlaybackByDefault === true;
}

export function selectionMarkerShiftButtonsEnabled(config: EditorRuntimeConfig): boolean {
  return config.selectionMarkerShiftButtonsEnabled === true;
}

export function visibleEditorButtons(config: EditorRuntimeConfig): EditorRuntimeConfig["visibleEditorButtons"] {
  return config.visibleEditorButtons;
}

export function editorButtonModes(config: EditorRuntimeConfig): EditorRuntimeConfig["editorButtonModes"] {
  return config.editorButtonModes;
}

export function audioFieldSource(config: EditorRuntimeConfig, ord: number): string | null {
  return config.audioFieldSources?.[ord] ?? null;
}
