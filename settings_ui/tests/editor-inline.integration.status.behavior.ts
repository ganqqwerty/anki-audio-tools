import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import {
  muteConsole,
  renderFields,
} from "./editor-inline.integration.helpers.js";

describe("editor inline status lifecycle", () => {
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

  it("consumes initial status once in the field controller", () => {
    const config = {
      audioFieldIndices: [0],
      initialStatusByField: {
        0: { kind: "info", message: "Closed settings." },
      },
    };
    initializeEditorRuntime(config);
    scan(config);

    const status = document.querySelector<HTMLElement>('[data-testid="aqe-status-0"]')!;
    expect(status).toHaveTextContent("Closed settings.");
    expect(status.dataset.statusOwner).toBe("edit");
    expect(window.__AQE_EDITOR_CONFIG__?.initialStatusByField?.[0]).toBeUndefined();

    status.textContent = "";
    scan(config);

    expect(status).toHaveTextContent("");
    expect(window.__AQE_EDITOR_CONFIG__?.initialStatusByField?.[0]).toBeUndefined();
  });
});
