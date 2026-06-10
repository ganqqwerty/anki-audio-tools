import { afterEach, describe, expect, it } from "vitest";
import {
  editorButtonModes,
  editorRuntimeConfig,
  repeatPlaybackByDefault,
  selectionMarkerShiftButtonsEnabled,
  splitButtonDefaults,
  visibleEditorButtons,
} from "../src/editor-inline/editor-runtime-config.js";
import { EditorButtonMode } from "../src/lib/types.js";
import type { EditorRuntimeConfig } from "../src/editor-inline/types.js";

describe("editor runtime config adapter", () => {
  afterEach(() => {
    delete (globalThis as Record<string, unknown>).__AQE_EDITOR_CONFIG__;
  });

  it("returns a safe fallback when Python has not injected config yet", () => {
    expect(editorRuntimeConfig()).toEqual({ audioFieldIndices: [] });
    expect(repeatPlaybackByDefault(editorRuntimeConfig())).toBe(false);
    expect(selectionMarkerShiftButtonsEnabled(editorRuntimeConfig())).toBe(false);
    expect(visibleEditorButtons(editorRuntimeConfig())).toBeUndefined();
    expect(editorButtonModes(editorRuntimeConfig())).toBeUndefined();
    expect(splitButtonDefaults(editorRuntimeConfig())).toEqual({});
  });

  it("returns injected config and stable derived values", () => {
    const injected: EditorRuntimeConfig = {
      audioFieldIndices: [0],
      editorButtonModes: { "aqe:play": EditorButtonMode.Icon },
      repeatPlaybackByDefault: true,
      selectionMarkerShiftButtonsEnabled: true,
      visibleEditorButtons: ["aqe:play", "aqe:analyze"],
    };
    globalThis.__AQE_EDITOR_CONFIG__ = injected;

    const config = editorRuntimeConfig();

    expect(config.audioFieldIndices).toEqual([0]);
    expect(repeatPlaybackByDefault(config)).toBe(true);
    expect(selectionMarkerShiftButtonsEnabled(config)).toBe(true);
    expect(visibleEditorButtons(config)).toEqual(["aqe:play", "aqe:analyze"]);
    expect(editorButtonModes(config)).toEqual({ "aqe:play": EditorButtonMode.Icon });
    expect(splitButtonDefaults(config)).toEqual({});
  });
});
