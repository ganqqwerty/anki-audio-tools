import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioSourceForNode,
  disposeEditorRuntime,
  fieldIndex,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { toolbarButtons } from "../src/lib/editor-toolbar-buttons.js";
import { settingsToolbarButtons } from "../src/lib/settings-toolbar-buttons.js";
import { muteConsole, renderFields } from "./editor-inline.integration.helpers.js";

describe("editor inline toolbar configuration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("mounts one Svelte control surface per explicit audio field", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    const graphButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!;
    const removePausesButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-remove-pauses"]')!;
    const showFileButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-show-file"]')!;
    const convertButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-convert"]')!;
    const denoiseButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')!;
    const pitchHumButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-pitch-hum"]')!;
    const slowerButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-slower"]')!;
    const fasterButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-faster"]')!;
    const settingsButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-settings"]')!;
    const volumeDownButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-down"]')!;
    const volumeUpButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!;
    expect(graphButton).toHaveClass("aqe-icon-only");
    expect(graphButton).toHaveAttribute("aria-label", "Graph\nDraw a pitch/intensity graph");
    expect(removePausesButton).not.toHaveClass("aqe-icon-only");
    expect(showFileButton).toHaveClass("aqe-icon-only");
    expect(convertButton).not.toHaveClass("aqe-icon-only");
    expect(denoiseButton).not.toHaveClass("aqe-icon-only");
    expect(pitchHumButton).not.toHaveClass("aqe-icon-only");
    expect(slowerButton).toHaveClass("aqe-icon-only");
    expect(fasterButton).toHaveClass("aqe-icon-only");
    expect(settingsButton).toHaveClass("aqe-icon-only");
    expect(volumeDownButton).toHaveClass("aqe-icon-only");
    expect(volumeUpButton).toHaveClass("aqe-icon-only");
    expect(document.querySelector('[data-testid="aqe-button-0-denoise-standard"]')).toHaveTextContent("Denoise");
    expect(document.querySelector('[data-testid="aqe-split-0-denoise-standard-menu"]')).toHaveTextContent("Options");
    expect(audioSourceForNode(document.getElementById("f0")!)).toBe("clip one.mp3");
    expect(fieldIndex(document.getElementById("f0")!, 7)).toBe(0);
  });

  it("defines toolbar commands in the configured sequence", () => {
    expect(toolbarButtons().map((button) => button.command)).toEqual([
      "aqe:play",
      "aqe:analyze",
      "aqe:show-file",
      "aqe:share",
      "aqe:preset",
      "aqe:denoise-standard",
      "aqe:remove-pauses",
      "aqe:slower",
      "aqe:faster",
      "aqe:volume-down",
      "aqe:volume-up",
      "aqe:chorusing-next",
      "aqe:chorusing-previous",
      "aqe:record-voice",
      "aqe:play-recording",
      "aqe:share-recording",
      "aqe:show-recording-file",
      "aqe:pitch-hum",
      "aqe:convert",
      "aqe:reduce-size",
      "aqe:undo",
      "aqe:redo",
      "aqe:settings",
    ]);

    expect(settingsToolbarButtons().map((button) => button.command)).toEqual([
      "aqe:play",
      "aqe:analyze",
      "aqe:show-file",
      "aqe:share",
      "aqe:preset",
      "aqe:denoise-standard",
      "aqe:remove-pauses",
      "aqe:slower",
      "aqe:faster",
      "aqe:volume-down",
      "aqe:volume-up",
      "aqe:chorusing-next",
      "aqe:chorusing-previous",
      "aqe:record-voice",
      "aqe:play-recording",
      "aqe:share-recording",
      "aqe:show-recording-file",
      "aqe:pitch-hum",
      "aqe:convert",
      "aqe:reduce-size",
      "aqe:delete-selection",
      "aqe:delete-rest",
      "aqe:undo",
      "aqe:redo",
      "aqe:settings",
    ]);
  });
});
