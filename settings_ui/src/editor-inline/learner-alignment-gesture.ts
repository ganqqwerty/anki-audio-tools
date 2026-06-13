import { startGestureSession } from "./gesture-session.js";
import { cursorMsFromEvent } from "./plot.js";
import type { VisualizerElement } from "./types.js";
import { readVisualizerTimeViewport } from "./visualizer-state.js";
import {
  readLearnerAlignmentOffsetMs,
  setLearnerAlignmentOffsetMs,
} from "./visualizer-renderer.js";

export function startLearnerAlignmentGesture(event: PointerEvent, visualizer: VisualizerElement): boolean {
  if (event.shiftKey || !eventTargetsLearnerPitch(event.target)) return false;
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const learner = visualizer.__aqeLearnerTrack;
  if (!svg || !learner) return false;

  event.preventDefault();
  event.stopPropagation();
  visualizer.dataset.learnerAlignmentDragging = "true";

  const viewport = readVisualizerTimeViewport(visualizer);
  const startPointerMs = cursorMsFromEvent(event, svg, viewport.durationMs, viewport);
  const startOffsetMs = readLearnerAlignmentOffsetMs(visualizer);

  const offsetFromEvent = (pointerEvent: PointerEvent): number => {
    const pointerMs = cursorMsFromEvent(pointerEvent, svg, viewport.durationMs, viewport);
    return startOffsetMs + pointerMs - startPointerMs;
  };

  startGestureSession({
    lostPointerCaptureTarget: svg,
    onCancel() {
      visualizer.dataset.learnerAlignmentDragging = "false";
      setLearnerAlignmentOffsetMs(visualizer, startOffsetMs);
    },
    onPointerMove(moveEvent) {
      setLearnerAlignmentOffsetMs(visualizer, offsetFromEvent(moveEvent));
    },
    onPointerUp(upEvent) {
      visualizer.dataset.learnerAlignmentDragging = "false";
      setLearnerAlignmentOffsetMs(visualizer, offsetFromEvent(upEvent));
    },
  });
  return true;
}

function eventTargetsLearnerPitch(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest(".aqe-learner-pitch-path") !== null;
}
