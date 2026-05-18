import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioSourceForNode,
  disposeEditorRuntime,
  explicitFieldTargets,
  fieldIndex,
  fieldNodes,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import type { EditorCommandPayload } from "../src/editor-inline/types.js";
import {
  bridgeCommands,
  muteConsole,
  renderFields,
  renderTwoAudioFields,
  track,
} from "./editor-inline.integration.helpers.js";

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
    const settingsButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-settings"]')!;
    expect(graphButton).toHaveClass("aqe-icon-only");
    expect(graphButton).toHaveAttribute("aria-label", "Analyze and show pitch/intensity graph");
    expect(settingsButton).toHaveClass("aqe-icon-only");
    expect(document.querySelector('[data-testid="aqe-button-0-denoise-standard"]')).toHaveTextContent("Denoise");
    expect(document.querySelector('[data-testid="aqe-split-0-denoise-standard-menu"]')).toHaveTextContent("Options");
    expect(audioSourceForNode(document.getElementById("f0")!)).toBe("clip one.mp3");
    expect(fieldIndex(document.getElementById("f0")!, 7)).toBe(0);
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

  it("dispatches denoise split commands and renders collapsed help", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const help = document.querySelector<HTMLDetailsElement>('[data-testid="aqe-help-0"]')!;
    expect(help.open).toBe(false);
    expect(help.querySelectorAll(".aqe-help-command")).toHaveLength(14);
    expect(help).toHaveTextContent("Shift-drag on the graph to select a region.");
    expect(help).toHaveTextContent("Delete Region removes only the selected region.");
    expect(help).toHaveTextContent("Every edit creates a new media file and updates the field to point at it.");
    expect(help).toHaveTextContent("grey is loudness and lines are pitch of the voice.");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')!.click();
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:denoise-standard",
      fieldOrd: 0,
      overrides: {
        denoiseAlgorithm: "standard",
      },
    });

    window.__aqePrepareForNewNote?.();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-denoise-standard-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-denoise-standard-preset-rnnoise"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')!.click();
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:rnnoise",
      fieldOrd: 0,
      overrides: {
        denoiseAlgorithm: "rnnoise",
      },
    });
  });

  it("dispatches trim commands with the field-local split value", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        speedStep: 0.05,
        trimStepMs: 200,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-trim-left"]')!.click();

    expect(bridgeCommands()).toContain("focus:0");
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toEqual({
      command: "aqe:trim-left",
      fieldOrd: 0,
      overrides: {
        trimStepMs: 200,
      },
    });
  });

  it("keeps trim split values isolated across audio fields", async () => {
    renderTwoAudioFields();
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0, 1],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        speedStep: 0.05,
        trimStepMs: 100,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-trim-left-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-trim-left-preset-200"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-trim-left"]')!.click();
    const firstPayload = window.__aqePendingCommandPayload;
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-1-trim-left"]')!.click();
    const secondPayload = window.__aqePendingCommandPayload;

    expect(bridgeCommands().filter((command) => command === "aqe:command-payload")).toHaveLength(2);
    expect([firstPayload, secondPayload].map((payload) => payload?.overrides?.trimStepMs)).toEqual([200, 100]);
  });

  it("dispatches volume and speed split payloads with local values", async () => {
    renderFields();
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        speedStep: 0.05,
        trimStepMs: 100,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-up-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-volume-up-preset-6"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();
    const volumePayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    window.__aqePendingCommandPayload = null;
    window.__aqeSetBusy?.(0, false);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-faster-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-faster-preset-0.1"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-faster"]')!.click();

    expect(volumePayload?.overrides?.volumeStepDb).toBe(6);
    const speedPayload = window.__aqePendingCommandPayload as EditorCommandPayload | null | undefined;
    expect(speedPayload?.overrides?.speedStep).toBe(0.1);
  });

  it("dispatches pause aggressiveness split payloads with local values", async () => {
    renderFields();
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        speedStep: 0.05,
        trimStepMs: 100,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-remove-pauses-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-remove-pauses-preset-aggressive"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-remove-pauses"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:remove-pauses",
      fieldOrd: 0,
      overrides: {
        pauseAggressiveness: "aggressive",
      },
    });
  });

  it("removes orphaned controls from previous bundle instances before mounting", () => {
    document.body.insertAdjacentHTML(
      "afterbegin",
      `
        <div class="aqe-mount-host">
          <div class="aqe-controls" data-aqe-field-ord="0">
            <div class="aqe-visualizer" data-aqe-field-ord="0" hidden data-graph-active="false"></div>
          </div>
        </div>
      `,
    );

    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);

    const visualizers = document.querySelectorAll<HTMLElement>('.aqe-visualizer[data-aqe-field-ord="0"]');
    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(visualizers).toHaveLength(1);
    expect(document.querySelector<HTMLElement>('.aqe-visualizer[data-aqe-field-ord="0"]')?.dataset.sourceFilename).toBe(
      "clip one.mp3",
    );
  });

  it("cancels delayed scans when the runtime is disposed", () => {
    vi.useFakeTimers();
    try {
      initializeEditorRuntime({ audioFieldIndices: [0] });
      disposeEditorRuntime();

      vi.runAllTimers();

      expect(document.querySelectorAll(".aqe-controls")).toHaveLength(0);
    } finally {
      vi.useRealTimers();
    }
  });

  it("preserves an existing explicit mount when a reload scan has no visible sound text", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    const controls = document.querySelector(".aqe-controls");

    document.getElementById("f0")!.textContent = "";
    scan({ audioFieldIndices: [0] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(document.querySelector(".aqe-controls")).toBe(controls);
  });

  it("auto-detects supported audio fields, dedupes rescans, and remounts changed sources", () => {
    document.body.innerHTML = `
      <div>
        <div contenteditable="true" data-field-ord="2">[sound:first.wav]</div>
      </div>
      <div>
        <div contenteditable="true" data-field-ord="3">[sound:video.mp4]</div>
      </div>
      <div><div contenteditable="true"></div></div>
    `;

    scan({ audioFieldIndices: [] });
    scan({ audioFieldIndices: [] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(document.querySelector(".aqe-controls")?.getAttribute("data-aqe-source-filename")).toBe("first.wav");
    expect(fieldNodes()).toHaveLength(2);
    expect(explicitFieldTargets([99])).toEqual([]);

    const field = document.querySelector<HTMLElement>('[data-field-ord="2"]')!;
    field.innerHTML = "[sound:second.ogg]";
    scan({ audioFieldIndices: [] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(document.querySelector(".aqe-controls")?.getAttribute("data-aqe-source-filename")).toBe("second.ogg");
  });

  it("renders repeat next to play and initializes it from runtime config", () => {
    initializeEditorRuntime({ audioFieldIndices: [0], repeatPlaybackByDefault: true });
    scan({ audioFieldIndices: [0], repeatPlaybackByDefault: true });

    const repeat = document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]');
    expect(repeat).toHaveAttribute("aria-pressed", "true");
    expect(repeat).toHaveClass("aqe-icon-only");

    repeat?.click();

    expect(window.__aqeGraphStateForTest?.(0)?.repeatEnabled).toBe(false);
    expect(repeat).toHaveAttribute("aria-pressed", "false");
  });

});
