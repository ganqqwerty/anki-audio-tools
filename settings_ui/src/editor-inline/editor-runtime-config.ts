import type { EditorRuntimeConfig, SplitButtonDefaults } from "./types.js";

const FALLBACK_EDITOR_RUNTIME_CONFIG: EditorRuntimeConfig = { audioFieldIndices: [] };

declare global {
  var __AQE_EDITOR_CONFIG__: EditorRuntimeConfig | undefined;
}

export function editorRuntimeConfig(): EditorRuntimeConfig {
  return globalThis.__AQE_EDITOR_CONFIG__ ?? FALLBACK_EDITOR_RUNTIME_CONFIG;
}

export function setEditorRuntimeConfig(config: EditorRuntimeConfig): EditorRuntimeConfig {
  globalThis.__AQE_EDITOR_CONFIG__ = config;
  return config;
}

export function updateEditorRuntimeConfig(values: Partial<EditorRuntimeConfig>): EditorRuntimeConfig {
  return setEditorRuntimeConfig({
    ...editorRuntimeConfig(),
    ...values,
  });
}

export function splitButtonDefaults(config: EditorRuntimeConfig): SplitButtonDefaults {
  return (config.splitButtonDefaults ?? {}) as SplitButtonDefaults;
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
