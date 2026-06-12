import { waitFor } from "@testing-library/svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { EditorButtonMode } from "../src/lib/types.js";
import {
  bridgeCommands,
  consumePendingCommandPayload,
  muteConsole,
  renderFields,
} from "./editor-inline.integration.helpers.js";

describe("editor inline toolbar controls", () => {
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

  it("disables undo and redo until history snapshots become available and updates their tooltips", () => {
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
      "Undo\nUndo the last action and restore the previous file\n\nNothing to undo yet",
    );
    expect(redoButton).toHaveAttribute(
      "aria-label",
      "Redo\nRedo the last undone action and restore the next file\n\nNothing to redo yet",
    );
    expect(undoTooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Undo\nUndo the last action and restore the previous file\n\nNothing to undo yet",
    );
    expect(redoTooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Redo\nRedo the last undone action and restore the next file\n\nNothing to redo yet",
    );

    window.__aqeSetHistorySnapshot?.(0, {
      canUndo: true,
      canRedo: false,
      undoItems: [{ id: "undo:1", label: "Shorten pauses" }],
      redoItems: [],
    });

    expect(undoButton).not.toBeDisabled();
    expect(redoButton).toBeDisabled();
    expect(undoButton).toHaveAttribute("aria-label", "Undo\nUndo the last action and restore the previous file");
    expect(redoButton).toHaveAttribute(
      "aria-label",
      "Redo\nRedo the last undone action and restore the next file\n\nNothing to redo yet",
    );
    expect(undoTooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Undo\nUndo the last action and restore the previous file",
    );
    expect(redoTooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Redo\nRedo the last undone action and restore the next file\n\nNothing to redo yet",
    );
  });

  it("opens undo history and dispatches a one-based history jump payload", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetHistorySnapshot?.(0, {
      canUndo: true,
      canRedo: false,
      undoItems: [
        { id: "undo:1", label: "Denoise" },
        { id: "undo:2", label: "Shorten pauses" },
      ],
      redoItems: [],
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-undo-menu"]')!.click();
    await waitFor(() => expect(document.querySelector('[data-testid="aqe-history-0-undo-2"]')).not.toBeNull());
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-history-0-undo-2"]')!.click();

    expect(consumePendingCommandPayload()).toEqual({
      command: "aqe:history-jump",
      direction: "undo",
      fieldOrd: 0,
      steps: 2,
    });
    expect(bridgeCommands()).toContain("aqe:command-payload");
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
      "Share\nShare this file online and copy the link to the clipboard",
    );
  });
});
