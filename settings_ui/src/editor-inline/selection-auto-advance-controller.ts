import { dispatchHtmlAudioSessionEvent } from "./html-audio-session-controller.js";
import { startSourcePlaybackAction } from "./source-playback-actions.js";
import { getSplitButtonState } from "./split-button-state.js";
import { selectionForVisualizer, setSelection as setSelectionFromController } from "./selection-controller.js";
import { notifySelectionChanged } from "./selection-events.js";
import { chorusingStateForVisualizer, writeChorusingState } from "./chorusing-dom.js";
import { resolveSelectionAutoAdvanceBoundary } from "./selection-auto-advance.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import type { LoopBoundaryResult } from "./playback-controller.js";
import type { PlaybackPass } from "./playback-model.js";
import type { VisualizerElement } from "./types.js";

export function handleSelectedRepeatAutoAdvanceBoundary(
  visualizer: VisualizerElement,
  pass: PlaybackPass,
): LoopBoundaryResult {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const selection = selectionForVisualizer(visualizer);
  if (!selection || pass.regionMode !== "selection") return false;
  const passAnchorMs = pass.regionMode === "selection" ? pass.resetCursorMs : pass.startMs;
  if (Math.round(passAnchorMs) !== Math.round(selection.startMs)) return false;
  if (Math.round(pass.endMs) !== Math.round(selection.endMs)) return false;

  const markerState = chorusingStateForVisualizer(visualizer);
  const splitState = getSplitButtonState(ord);
  const decision = resolveSelectionAutoAdvanceBoundary({
    autoAdvance: splitState.chorusingAutoAdvance,
    markersMs: markerState.markersMs,
    repeatCount: splitState.chorusingRepeatCount,
    repeatPassesCompleted: markerState.repeatPassesCompleted,
    selection,
  });

  writeChorusingState(visualizer, {
    ...markerState,
    fullBaseSelectionActive: decision.nextSelection
      ? isBaseSelection(markerState, decision.nextSelection)
      : markerState.fullBaseSelectionActive,
    repeatPassesCompleted: decision.nextRepeatPassesCompleted,
  });

  if (decision.action === "ignore") return false;
  if (decision.action === "repeat") return false;
  if (decision.action === "complete") {
    dispatchHtmlAudioSessionEvent(ord, {
      cursorMs: selection.startMs,
      type: "StopRequested",
    });
    return "complete";
  }
  if (!decision.nextSelection) return false;
  setSelectionFromController(
    visualizer,
    decision.nextSelection.startMs,
    decision.nextSelection.endMs,
    { setCursor: () => undefined },
    { updateCursor: false },
  );
  syncSelectionToolbar(visualizer);
  notifySelectionChanged(visualizer, "chorusing");
  startSourcePlaybackAction(visualizer, {
    action: "start",
    cursorMs: Math.round(decision.nextSelection.startMs),
    endMs: Math.round(decision.nextSelection.endMs),
    engine: "html",
    loop: true,
    ord,
    regionMode: "selection",
    source: "user",
  });
  return "handled";
}

function isBaseSelection(
  state: ReturnType<typeof chorusingStateForVisualizer>,
  selection: { startMs: number; endMs: number },
): boolean {
  return Boolean(
    state.baseRegion
    && Math.round(selection.startMs) <= Math.round(state.baseRegion.startMs)
    && Math.round(selection.endMs) >= Math.round(state.baseRegion.endMs),
  );
}
