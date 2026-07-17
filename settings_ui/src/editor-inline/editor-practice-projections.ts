import {
  chorusingStateForVisualizer,
  writeChorusingState,
} from "./chorusing-dom.js";
import { visualizerForOrd } from "./dom-selectors.js";
import {
  clearRepeatPauseCountdownOverlay,
  startRepeatPauseCountdownOverlay,
} from "./graph-countdown-overlay.js";
import { publishRepeatWaitingState } from "./html-audio-session-field-projection.js";
import type { PracticeRange, PracticeRuntimeSnapshot } from "./practice/index.js";
import { setLearnerRecordingState } from "./recording-actions-state.js";
import { setSelection } from "./selection-controller.js";
import { notifySelectionChanged } from "./selection-events.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";

export interface PracticeRecordingProjection {
  readonly fieldOrd: number;
  readonly startCursorMs: number;
  readonly targetDurationMs: number;
}

export function projectPracticeSelection(fieldOrd: number, range: PracticeRange): void {
  const visualizer = visualizerForOrd(fieldOrd);
  if (!visualizer) return;
  const markerState = chorusingStateForVisualizer(visualizer);
  writeChorusingState(visualizer, {
    ...markerState,
    fullBaseSelectionActive: Boolean(
      markerState.baseRegion
      && range.startMs <= markerState.baseRegion.startMs
      && range.endMs >= markerState.baseRegion.endMs
    ),
    repeatPassesCompleted: 0,
  });
  setSelection(
    visualizer,
    range.startMs,
    range.endMs,
    { setCursor: () => undefined },
    { updateCursor: false },
  );
  syncSelectionToolbar(visualizer);
  notifySelectionChanged(visualizer, "chorusing");
}

export function projectPracticeWait(
  fieldOrd: number,
  durationMs: number,
  waiting: boolean,
  purpose: "countdown" | "repeat_gap",
  recording: PracticeRecordingProjection | null,
  resetCursorMs: number,
): void {
  const visualizer = visualizerForOrd(fieldOrd);
  if (purpose === "repeat_gap") {
    if (!visualizer) return;
    if (waiting) {
      publishRepeatWaitingState(fieldOrd, resetCursorMs, null);
      startRepeatPauseCountdownOverlay(visualizer, durationMs);
    } else {
      clearRepeatPauseCountdownOverlay(visualizer);
    }
    return;
  }
  if (!recording || recording.fieldOrd !== fieldOrd || !waiting) return;
  setLearnerRecordingState({
    countdownSeconds: Math.ceil(durationMs / 1000),
    fieldOrd,
    startCursorMs: recording.startCursorMs,
    status: "countdown",
    targetDurationMs: recording.targetDurationMs,
  });
}

export function projectPracticeChorusingState(
  fieldOrd: number,
  snapshot: PracticeRuntimeSnapshot | null,
): void {
  if (!snapshot || snapshot.state.kind !== "chorusing" || snapshot.state.pass.ord !== fieldOrd) {
    return;
  }
  const visualizer = visualizerForOrd(fieldOrd);
  if (!visualizer) return;
  writeChorusingState(visualizer, {
    ...chorusingStateForVisualizer(visualizer),
    repeatPassesCompleted: snapshot.state.completedPasses,
  });
}
