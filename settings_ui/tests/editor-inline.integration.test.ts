import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioSourceForNode,
  disposeEditorRuntime,
  fieldIndex,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { muteConsole, renderFields } from "./editor-inline.integration.helpers.js";

describe("editor inline Svelte integration", () => {
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
    expect(graphButton).toHaveAttribute("aria-label", "Analyze and show pitch/intensity graph");
    expect(removePausesButton).toHaveClass("aqe-icon-only");
    expect(showFileButton).toHaveClass("aqe-icon-only");
    expect(convertButton).toHaveClass("aqe-icon-only");
    expect(denoiseButton).toHaveClass("aqe-icon-only");
    expect(pitchHumButton).toHaveClass("aqe-icon-only");
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

  it("hides toolbar buttons omitted from visible editor button config", () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      visibleEditorButtons: ["aqe:play", "aqe:analyze", "aqe:trim-left"],
    });
    scan({
      audioFieldIndices: [0],
      visibleEditorButtons: ["aqe:play", "aqe:analyze", "aqe:trim-left"],
    });

    expect(document.querySelector('[data-testid="aqe-button-0-play"]')).toBeInTheDocument();
    expect(document.querySelector('[data-testid="aqe-button-0-graph"]')).toBeInTheDocument();
    expect(document.querySelector('[data-testid="aqe-button-0-trim-left"]')).toBeInTheDocument();
    expect(document.querySelector('[data-testid="aqe-button-0-settings"]')).not.toBeInTheDocument();
    expect(document.querySelector('[data-testid="aqe-button-0-denoise-standard"]')).not.toBeInTheDocument();
  });

  it.each(["aac", "flac", "m4a", "mp3", "oga", "ogg", "opus", "wav", "webm"])(
    "detects %s sound references as supported audio",
    (extension) => {
      document.body.innerHTML = `<div id="format-field">[sound:clip one.${extension.toUpperCase()}]</div>`;

      expect(audioSourceForNode(document.getElementById("format-field")!)).toBe(
        `clip one.${extension.toUpperCase()}`,
      );
    },
  );

  it("does not detect mp4 sound references as supported audio", () => {
    document.body.innerHTML = '<div id="video-field">[sound:clip.mp4]</div>';

    expect(audioSourceForNode(document.getElementById("video-field")!)).toBe("");
  });
});
