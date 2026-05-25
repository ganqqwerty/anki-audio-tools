import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioSourceForNode,
  disposeEditorRuntime,
  fieldIndex,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { EditorButtonMode } from "../src/lib/types.js";
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

  it("renders one canonical status element after the visualizer", () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    });
    scan({
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    });

    const controls = document.querySelector<HTMLElement>('[data-testid="aqe-controls-0"]')!;
    const status = document.querySelector<HTMLElement>('[data-testid="aqe-status-0"]')!;
    const statusRow = controls.querySelector<HTMLElement>(".aqe-status-row")!;
    const visualizer = controls.querySelector<HTMLElement>(".aqe-visualizer")!;

    expect(controls.querySelectorAll(".aqe-status")).toHaveLength(1);
    expect(statusRow.querySelector('[data-testid="aqe-status-0"]')).toBe(status);
    expect(visualizer.querySelector('[data-testid="aqe-status-0"]')).toBeNull();
    expect(visualizer.hidden).toBe(true);
    expect(status).toHaveTextContent("Closed settings.");
  });

  it("disables undo and redo until history becomes available and updates their tooltips", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const undoButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-undo"]')!;
    const redoButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-redo"]')!;
    const undoTooltip = undoButton.closest<HTMLElement>(".aqe-button-tooltip-target");
    const redoTooltip = redoButton.closest<HTMLElement>(".aqe-button-tooltip-target");

    expect(undoButton).toBeDisabled();
    expect(redoButton).toBeDisabled();
    expect(undoButton).toHaveAttribute("aria-label", "Nothing to undo yet");
    expect(redoButton).toHaveAttribute("aria-label", "Nothing to redo yet");
    expect(undoTooltip).toHaveAttribute("data-aqe-tooltip-content", "Nothing to undo yet");
    expect(redoTooltip).toHaveAttribute("data-aqe-tooltip-content", "Nothing to redo yet");

    window.__aqeSetHistoryAvailability?.(0, true, false);

    expect(undoButton).not.toBeDisabled();
    expect(redoButton).toBeDisabled();
    expect(undoButton).toHaveAttribute("aria-label", "Undo the last action and restore the previous file");
    expect(redoButton).toHaveAttribute("aria-label", "Nothing to redo yet");
    expect(undoTooltip).toHaveAttribute("data-aqe-tooltip-content", "Undo the last action and restore the previous file");
    expect(redoTooltip).toHaveAttribute("data-aqe-tooltip-content", "Nothing to redo yet");
  });

  it("renders configured buttons as icon only", () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      editorButtonModes: {
        "aqe:play": EditorButtonMode.Icon,
        "aqe:analyze": EditorButtonMode.Icon,
      },
    });
    scan({
      audioFieldIndices: [0],
      editorButtonModes: {
        "aqe:play": EditorButtonMode.Icon,
        "aqe:analyze": EditorButtonMode.Icon,
      },
    });

    expect(document.querySelector('[data-testid="aqe-button-0-play"]')).toHaveClass("aqe-icon-only");
    expect(document.querySelector('[data-testid="aqe-button-0-graph"]')).toHaveClass("aqe-icon-only");
    expect(document.querySelector('[data-testid="aqe-button-0-settings"]')).toHaveClass("aqe-icon-only");
  });

  it("hides toolbar buttons omitted from visible editor button config", () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      visibleEditorButtons: ["aqe:play", "aqe:analyze", "aqe:convert"],
    });
    scan({
      audioFieldIndices: [0],
      visibleEditorButtons: ["aqe:play", "aqe:analyze", "aqe:convert"],
    });

    expect(document.querySelector('[data-testid="aqe-button-0-play"]')).toBeInTheDocument();
    expect(document.querySelector('[data-testid="aqe-button-0-graph"]')).toBeInTheDocument();
    expect(document.querySelector('[data-testid="aqe-button-0-convert"]')).toBeInTheDocument();
    expect(document.querySelector('[data-testid="aqe-button-0-settings"]')).not.toBeInTheDocument();
    expect(document.querySelector('[data-testid="aqe-button-0-denoise-standard"]')).not.toBeInTheDocument();
  });

  it("mounts the share split button in the default toolbar", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const shareButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-share"]');
    const shareMenuButton = document.querySelector<HTMLButtonElement>(
      '[data-testid="aqe-split-0-share-menu"]',
    );

    expect(shareButton).toBeInTheDocument();
    expect(shareMenuButton).toBeInTheDocument();
    expect(shareButton).toHaveAttribute(
      "aria-label",
      "Upload the current audio to Catbox or Litterbox and copy a public link",
    );
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
