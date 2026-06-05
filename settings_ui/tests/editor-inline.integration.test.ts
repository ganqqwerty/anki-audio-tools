import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioSourceForNode,
  disposeEditorRuntime,
  fieldIndex,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { EditorButtonMode } from "../src/lib/types.js";
import {
  commandLog,
  dragGraphSelection,
  graphClientX,
  muteConsole,
  renderFields,
  setGraphBounds,
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
    expect(graphButton).toHaveAttribute("aria-label", "Draw a pitch/intensity graph");
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
    expect(undoButton).toHaveAttribute(
      "aria-label",
      "Undo the last action and restore the previous file\n\nNothing to undo yet",
    );
    expect(redoButton).toHaveAttribute(
      "aria-label",
      "Redo the last undone action and restore the next file\n\nNothing to redo yet",
    );
    expect(undoTooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Undo the last action and restore the previous file\n\nNothing to undo yet",
    );
    expect(redoTooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Redo the last undone action and restore the next file\n\nNothing to redo yet",
    );

    window.__aqeSetHistoryAvailability?.(0, true, false);

    expect(undoButton).not.toBeDisabled();
    expect(redoButton).toBeDisabled();
    expect(undoButton).toHaveAttribute("aria-label", "Undo the last action and restore the previous file");
    expect(redoButton).toHaveAttribute(
      "aria-label",
      "Redo the last undone action and restore the next file\n\nNothing to redo yet",
    );
    expect(undoTooltip).toHaveAttribute("data-aqe-tooltip-content", "Undo the last action and restore the previous file");
    expect(redoTooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Redo the last undone action and restore the next file\n\nNothing to redo yet",
    );
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

  it("renders chorusing toolbar buttons as one labeled panel", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const panel = document.querySelector<HTMLElement>('[data-testid="aqe-chorusing-toolbar-panel-0"]')!;
    const practiceButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-practice"]')!;
    const previousButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-previous"]')!;
    const nextButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-next"]')!;

    expect(panel).toHaveClass("aqe-toolbar-panel", "aqe-chorusing-toolbar-panel");
    expect(panel).toHaveAttribute("role", "group");
    expect(panel).toHaveAttribute("aria-label", "Chorusing");
    expect(panel).toHaveAttribute("data-aqe-toolbar-button-container", "true");
    const panelLabel = panel.querySelector<HTMLElement>(".aqe-toolbar-panel-label");
    expect(panelLabel).toHaveTextContent("Chorusing");
    expect(panelLabel).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Practice the audio from the end, word by word, until you can repeat the whole sentence.",
    );
    expect(Array.from(panel.querySelectorAll<HTMLButtonElement>("[data-aqe-command]")).map((button) => button.dataset.aqeCommand)).toEqual([
      "aqe:chorusing-practice",
      "aqe:chorusing-next",
      "aqe:chorusing-previous",
    ]);
    expect(panel).toContainElement(practiceButton);
    expect(panel).toContainElement(previousButton);
    expect(panel).toContainElement(nextButton);
    expect(previousButton).toBeDisabled();
    expect(nextButton).toBeDisabled();
  });

  it("zooms, fits, and zooms to selection from graph controls", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-in-0"]')?.click();
    let state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(0);
    expect(state?.viewportEndMs).toBeLessThan(track.durationMs);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-fit-0"]')?.click();
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);

    dragGraphSelection(svg, 0.25, 0.5);
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-selection-0"]')?.click();
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeLessThanOrEqual(state?.selectionStartMs ?? 0);
    expect(state?.viewportEndMs).toBeGreaterThanOrEqual(state?.selectionEndMs ?? 0);
    expect((state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0)).toBeLessThan(track.durationMs);
  });

  it("uses graph wheel and keyboard gestures for horizontal zoom only", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const plot = document.querySelector<HTMLElement>('[data-testid="aqe-visualizer-plot-0"]')!;
    setGraphBounds(svg);

    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      ctrlKey: true,
      deltaY: -100,
    }));
    let state = window.__aqeGraphStateForTest?.(0);
    let span = (state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0);
    expect(span).toBeLessThan(track.durationMs);
    expect(span).toBeGreaterThan(track.durationMs * 0.75);

    const beforeShiftPanStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaX: 100,
      shiftKey: true,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeGreaterThan(beforeShiftPanStart);

    const beforePanStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaX: -100,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBeLessThan(beforePanStart);

    const beforeVerticalStart = state?.viewportStartMs ?? 0;
    plot.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true,
      clientX: graphClientX(svg, 0.5),
      deltaY: 100,
    }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(beforeVerticalStart);
    span = (state?.viewportEndMs ?? 0) - (state?.viewportStartMs ?? 0);
    expect(span).toBeGreaterThan(track.durationMs * 0.75);

    const visualizer = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    visualizer.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "0" }));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(track.durationMs);
  });

  it("scrolls the visible time viewport with a horizontal scrollbar", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const scrollbar = document.querySelector<HTMLElement>('[data-testid="aqe-time-scrollbar-0"]')!;
    const scrollport = document.querySelector<HTMLDivElement>('[data-testid="aqe-time-scrollbar-scroll-0"]')!;
    Object.defineProperty(scrollport, "clientWidth", { configurable: true, value: 200 });

    expect(scrollbar.hidden).toBe(true);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-zoom-in-0"]')?.click();
    await Promise.resolve();
    await Promise.resolve();
    expect(scrollbar.hidden).toBe(false);
    const beforeScroll = window.__aqeGraphStateForTest?.(0);
    expect(scrollport.querySelector<HTMLElement>(".aqe-time-scrollbar-spacer")?.style.width).toBe("125%");

    scrollport.scrollLeft = 50;
    scrollport.dispatchEvent(new Event("scroll"));

    const afterScroll = window.__aqeGraphStateForTest?.(0);
    expect(afterScroll?.viewportStartMs).toBeGreaterThan(beforeScroll?.viewportStartMs ?? 0);
    expect(afterScroll?.viewportEndMs).toBe(track.durationMs);
  });

  it("projects and hides the stopped cursor against the zoomed viewport", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 500);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    window.__aqeSetTimeViewportForTest?.(0, 250, 750);
    window.__aqeSetCursorForTest?.(0, 600, false);
    let state = window.__aqeGraphStateForTest?.(0);

    expect(state).toMatchObject({
      cursorMs: 600,
      progressMs: 600,
      timecodeFlagCurrent: "600 ms",
      timecodeFlagPitch: " / 260 Hz",
      timecodeFlagVisible: true,
    });
    expect(state?.cursorX).toBeCloseTo(44 + 566 * 0.7);

    window.__aqeSetCursorForTest?.(0, 900, false);
    state = window.__aqeGraphStateForTest?.(0);

    expect(state).toMatchObject({
      cursorMs: 900,
      progressMs: 900,
      timecodeFlagCurrent: "900 ms",
      timecodeFlagVisible: false,
    });
  });

  it("scrolls away from and back to the stopped cursor without committing cursor state", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const scrollport = document.querySelector<HTMLDivElement>('[data-testid="aqe-time-scrollbar-scroll-0"]')!;
    Object.defineProperty(scrollport, "clientWidth", { configurable: true, value: 200 });
    setGraphBounds(svg);
    window.__aqeSetTimeViewportForTest?.(0, 0, 500);
    window.__aqeSetCursorForTest?.(0, 250, false);
    await Promise.resolve();
    await Promise.resolve();
    const commandsBeforeScroll = commandLog().slice();

    scrollport.scrollLeft = 200;
    scrollport.dispatchEvent(new Event("scroll"));
    let state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      cursorMs: 250,
      timecodeFlagVisible: false,
      viewportEndMs: 1000,
      viewportStartMs: 500,
    });

    scrollport.scrollLeft = 0;
    scrollport.dispatchEvent(new Event("scroll"));
    state = window.__aqeGraphStateForTest?.(0);
    expect(state).toMatchObject({
      cursorMs: 250,
      timecodeFlagVisible: true,
      viewportEndMs: 500,
      viewportStartMs: 0,
    });
    expect(state?.cursorX).toBeCloseTo(44 + 566 * 0.5);
    expect(commandLog().slice(commandsBeforeScroll.length)).not.toContain("aqe:set-cursor");
  });

  it("resets zoom to fit when a graph is redrawn for a new track", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);

    window.__aqeSetVisualizer?.(0, { ...track, durationMs: 2000, sourceFilename: "next.mp3" }, 0);

    const state = window.__aqeGraphStateForTest?.(0);
    expect(state?.viewportStartMs).toBe(0);
    expect(state?.viewportEndMs).toBe(2000);
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
      "Share this file online and copy the link to the clipboard",
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
