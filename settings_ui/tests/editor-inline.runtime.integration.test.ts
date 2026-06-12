import {afterEach, beforeEach, describe, expect, it, vi} from "vitest";

import {
    disposeEditorRuntime,
    explicitFieldTargets,
    fieldNodes,
    initializeEditorRuntime,
    scan,
} from "../src/editor-inline/runtime.js";
import {muteConsole, renderFields, track} from "./editor-inline.integration.helpers.js";

describe("editor inline runtime scan integration", () => {
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

        initializeEditorRuntime({audioFieldIndices: [0]});
        scan({audioFieldIndices: [0]});
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
            initializeEditorRuntime({audioFieldIndices: [0]});
            disposeEditorRuntime();

            vi.runAllTimers();

            expect(document.querySelectorAll(".aqe-controls")).toHaveLength(0);
        } finally {
            vi.useRealTimers();
        }
    });

    it("preserves an existing explicit mount when a reload scan has no visible sound text", () => {
        initializeEditorRuntime({audioFieldIndices: [0]});
        scan({audioFieldIndices: [0]});
        const controls = document.querySelector(".aqe-controls");

        document.getElementById("f0")!.textContent = "";
        scan({audioFieldIndices: [0]});

        expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
        expect(document.querySelector(".aqe-controls")).toBe(controls);
    });

    it("clears viewport state when preparing for a new note", async () => {
        initializeEditorRuntime({audioFieldIndices: [0]});
        scan({audioFieldIndices: [0]});
        await Promise.resolve();
        window.__aqeSetVisualizer?.(0, track, 0);
        window.__aqeSetTimeViewportForTest?.(0, 250, 750);

        window.__aqePrepareForNewNote?.();

        const state = window.__aqeGraphStateForTest?.(0);
        expect(state?.viewportStartMs).toBe(0);
        expect(state?.viewportEndMs).toBe(0);
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

        scan({audioFieldIndices: []});
        scan({audioFieldIndices: []});

        expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
        expect(document.querySelector(".aqe-controls")?.getAttribute("data-aqe-source-filename")).toBe("first.wav");
        expect(fieldNodes()).toHaveLength(2);
        expect(explicitFieldTargets([99])).toEqual([]);

        const field = document.querySelector<HTMLElement>('[data-field-ord="2"]')!;
        field.innerHTML = "[sound:second.ogg]";
        scan({audioFieldIndices: []});

        expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
        expect(document.querySelector(".aqe-controls")?.getAttribute("data-aqe-source-filename")).toBe("second.ogg");
    });

    it("mounts explicit audio controls when field containers appear after scheduled scans", async () => {
        vi.useFakeTimers();
        try {
            document.body.innerHTML = `<main id="editor-root"></main>`;

            initializeEditorRuntime({
                audioFieldIndices: [1],
                audioFieldSources: {1: "late-field.wav"},
                showGraphByDefault: false,
            });

            vi.runOnlyPendingTimers();
            expect(document.querySelectorAll(".aqe-controls")).toHaveLength(0);

            document.getElementById("editor-root")!.insertAdjacentHTML(
                "beforeend",
                `
            <div class="field-container" data-index="1">
              <div contenteditable="true">Answer [sound:late-field.wav]</div>
            </div>
            `,
            );

            await Promise.resolve();
            vi.runOnlyPendingTimers();

            expect(document.querySelectorAll('.aqe-controls[data-aqe-field-ord="1"]')).toHaveLength(1);
            expect(document.querySelector(".aqe-controls")?.getAttribute("data-aqe-source-filename")).toBe("late-field.wav");
        } finally {
            vi.useRealTimers();
        }
    });
});
