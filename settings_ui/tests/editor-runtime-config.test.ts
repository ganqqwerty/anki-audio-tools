import { afterEach, describe, expect, it } from "vitest";
import {
  editorButtonModes,
  editorRuntimeConfig,
  repeatPlaybackByDefault,
  selectionMarkerShiftButtonsEnabled,
  splitButtonDefaults,
  visibleEditorButtons,
} from "../src/editor-inline/editor-runtime-config.js";

describe("editor runtime config adapter", () => {
  afterEach(() => {
    delete window.__AQE_EDITOR_CONFIG__;
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
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      editorButtonModes: { "aqe:play": "icon" },
      repeatPlaybackByDefault: true,
      selectionMarkerShiftButtonsEnabled: true,
      splitButtonDefaults: { outputFormat: "mp3", repeatPauseSeconds: 1.5 },
      visibleEditorButtons: ["aqe:play", "aqe:analyze"],
    };

    const config = editorRuntimeConfig();

    expect(config.audioFieldIndices).toEqual([0]);
    expect(repeatPlaybackByDefault(config)).toBe(true);
    expect(selectionMarkerShiftButtonsEnabled(config)).toBe(true);
    expect(visibleEditorButtons(config)).toEqual(["aqe:play", "aqe:analyze"]);
    expect(editorButtonModes(config)).toEqual({ "aqe:play": "icon" });
    expect(splitButtonDefaults(config)).toEqual({ outputFormat: "mp3", repeatPauseSeconds: 1.5 });
  });
});
