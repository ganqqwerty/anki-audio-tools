import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import {
  dispatchHandlePointer,
  graphClientX,
  muteConsole,
  renderFields,
  setFullGraphViewport,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";
import {
  initAndScan,
  recordingConfig,
  setupAudioTrack,
} from "./editor-inline.recording.integration.helpers.js";

describe("editor inline learner pitch alignment", () => {
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

  async function setupLearnerAlignmentGraph(): Promise<{
    svg: SVGSVGElement;
  }> {
    initAndScan(recordingConfig());
    await setupAudioTrack();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    setFullGraphViewport();
    window.__aqeSetLearnerRecordingState?.({
      fieldOrd: 0,
      generation: 1,
      startCursorMs: 0,
      status: "ready",
      targetDurationMs: track.durationMs,
    });
    window.__aqeSetLearnerVisualizer?.(0, track);
    return { svg };
  }

  function startLearnerDrag(learnerPath: SVGPathElement, svg: SVGSVGElement, ratio: number): void {
    const EventCtor = window.PointerEvent || window.MouseEvent;
    learnerPath.dispatchEvent(new EventCtor("pointerdown", {
      bubbles: true,
      clientX: graphClientX(svg, ratio),
      clientY: 40,
    }));
  }

  function graphState() {
    return window.__aqeGraphStateForTest?.(0);
  }

  function learnerPath(): SVGPathElement {
    return document.querySelector<SVGPathElement>(".aqe-learner-pitch-path")!;
  }

  function visualizer(): HTMLElement {
    return document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
  }

  it("drags the learner pitch path horizontally without moving the playback cursor", async () => {
    const { svg } = await setupLearnerAlignmentGraph();
    const startPath = learnerPath().getAttribute("d") || "";

    startLearnerDrag(learnerPath(), svg, 0.5);
    dispatchHandlePointer(learnerPath(), "pointermove", graphClientX(svg, 0.3));
    dispatchHandlePointer(learnerPath(), "pointerup", graphClientX(svg, 0.3));

    const movedPath = document.querySelector<SVGPathElement>(".aqe-learner-pitch-path")?.getAttribute("d") || "";
    expect(graphState()).toMatchObject({
      cursorMs: 0,
      learnerAlignmentOffsetMs: -200,
    });
    expect(movedPath).not.toBe(startPath);
    expect(movedPath).toContain("L 10.00");
  });

  it("restores the starting offset on pointer cancel", async () => {
    const { svg } = await setupLearnerAlignmentGraph();

    startLearnerDrag(learnerPath(), svg, 0.5);
    dispatchHandlePointer(learnerPath(), "pointerup", graphClientX(svg, 0.6));
    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: 100 });

    startLearnerDrag(learnerPath(), svg, 0.6);
    dispatchHandlePointer(learnerPath(), "pointermove", graphClientX(svg, 0.2));
    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: -300 });
    expect(visualizer().dataset.learnerAlignmentDragging).toBe("true");

    dispatchHandlePointer(learnerPath(), "pointercancel", graphClientX(svg, 0.2));

    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: 100 });
    expect(visualizer().dataset.learnerAlignmentDragging).toBe("false");
  });

  it("restores the starting offset on lost pointer capture", async () => {
    const { svg } = await setupLearnerAlignmentGraph();
    const EventCtor = window.PointerEvent || window.MouseEvent;

    startLearnerDrag(learnerPath(), svg, 0.5);
    dispatchHandlePointer(learnerPath(), "pointerup", graphClientX(svg, 0.6));
    startLearnerDrag(learnerPath(), svg, 0.6);
    dispatchHandlePointer(learnerPath(), "pointermove", graphClientX(svg, 0.9));
    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: 400 });

    svg.dispatchEvent(new EventCtor("lostpointercapture", {
      bubbles: true,
      clientX: graphClientX(svg, 0.9),
    }));

    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: 100 });
    expect(visualizer().dataset.learnerAlignmentDragging).toBe("false");
  });

  it("restores the starting offset on window blur", async () => {
    const { svg } = await setupLearnerAlignmentGraph();

    startLearnerDrag(learnerPath(), svg, 0.5);
    dispatchHandlePointer(learnerPath(), "pointerup", graphClientX(svg, 0.6));
    startLearnerDrag(learnerPath(), svg, 0.6);
    dispatchHandlePointer(learnerPath(), "pointermove", graphClientX(svg, 0.1));
    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: -400 });

    window.dispatchEvent(new Event("blur"));

    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: 100 });
    expect(visualizer().dataset.learnerAlignmentDragging).toBe("false");
  });

  it("clamps learner dragging cleanly at both graph bounds", async () => {
    const { svg } = await setupLearnerAlignmentGraph();

    startLearnerDrag(learnerPath(), svg, 0.5);
    dispatchHandlePointer(learnerPath(), "pointerup", graphClientX(svg, -0.2));
    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: -500 });

    startLearnerDrag(learnerPath(), svg, 0);
    dispatchHandlePointer(learnerPath(), "pointerup", graphClientX(svg, 1.3));
    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: 500 });
  });

  it("uses the final pointer position after multiple moves and direction reversal", async () => {
    const { svg } = await setupLearnerAlignmentGraph();

    startLearnerDrag(learnerPath(), svg, 0.5);
    dispatchHandlePointer(learnerPath(), "pointermove", graphClientX(svg, 0.8));
    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: 300 });
    dispatchHandlePointer(learnerPath(), "pointermove", graphClientX(svg, 0.4));
    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: -100 });
    dispatchHandlePointer(learnerPath(), "pointerup", graphClientX(svg, 0.7));

    expect(graphState()).toMatchObject({ learnerAlignmentOffsetMs: 200 });
    expect(visualizer().dataset.learnerAlignmentDragging).toBe("false");
  });
});
