import { visualizerForOrd } from "./dom-selectors.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import {
  shouldTreatSelectionGestureAsClick as isClickLikeSelectionGesture,
  type SelectionResizeEdge,
} from "./selection-state.js";
import { notifySelectionChanged, type SelectionMutationOrigin } from "./selection-events.js";
import { chorusingStateForVisualizer } from "./chorusing-dom.js";
import {
  resolveSelectionMarkerShift,
  type SelectionShiftDirection,
  type SelectionShiftEdge,
} from "./selection-marker-shift.js";
import {
  clearSelection as clearSelectionFromController,
  clearSelectionDraft as clearSelectionDraftFromController,
  commitSelectionDraft as commitSelectionDraftFromController,
  draftSelectionForVisualizer as draftSelectionForVisualizerFromController,
  effectivePlaybackRegion as effectivePlaybackRegionFromController,
  selectionForVisualizer as selectionForVisualizerFromController,
  setSelection as setSelectionFromController,
  setSelectionDraft as setSelectionDraftFromController,
  type SelectionControllerDependencies,
} from "./selection-controller.js";
import {
  handleVisualizerPointerDown as handleVisualizerPointerDownGesture,
  startCursorDrag as startCursorDragGesture,
  startSelectionResizeGesture as startSelectionResizeGestureFlow,
  startSelectionGesture as startSelectionGestureFlow,
  type SelectionGestureDependencies,
} from "./selection-gestures.js";
import { playbackStateFor, startEditorHtmlPlayback, stopProgressClock } from "./playback-actions.js";
import { currentProgressMs } from "./playback-actions.js";
import { readVisualizerTargetDurationMs, setVisualizerResumeRequiresRestart } from "./visualizer-state.js";
import { audioClockReady } from "./actions-audio-clock.js";
import { seekAudioClock } from "./actions-playback.js";
import { playbackRequestForStart, setCursor } from "./actions-playback.js";
import type { PlaybackRegion } from "./playback-state.js";
import type { VisualizerElement } from "./types.js";

export function selectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  return selectionForVisualizerFromController(visualizer);
}

export function draftSelectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  return draftSelectionForVisualizerFromController(visualizer);
}

export function effectivePlaybackRegion(visualizer: VisualizerElement): PlaybackRegion {
  return effectivePlaybackRegionFromController(visualizer);
}

export function clearSelectionDraft(
  visualizer: VisualizerElement,
  options: { redraw?: boolean } = {},
): void {
  clearSelectionDraftFromController(visualizer, options);
  syncSelectionToolbar(visualizer);
}

export function setSelectionDraft(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  options: { redraw?: boolean } = {},
): boolean {
  const drafted = setSelectionDraftFromController(visualizer, startMs, endMs, options);
  syncSelectionToolbar(visualizer);
  return drafted;
}

export function commitSelectionDraft(
  visualizer: VisualizerElement,
  options: { origin?: SelectionMutationOrigin; updateCursor?: boolean } = {},
): boolean {
  const committed = commitSelectionDraftFromController(visualizer, selectionControllerDependencies(), options);
  if (committed) notifySelectionChanged(visualizer, options.origin ?? "user");
  syncSelectionToolbar(visualizer);
  return committed;
}

export function clearSelection(
  visualizer: VisualizerElement,
  options: { origin?: SelectionMutationOrigin; resetPlaybackRegion?: boolean } = {},
): void {
  clearSelectionFromController(visualizer, options);
  notifySelectionChanged(visualizer, options.origin ?? "user");
  syncSelectionToolbar(visualizer);
}

export function setSelection(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  options: { origin?: SelectionMutationOrigin; updateCursor?: boolean } = {},
): boolean {
  const selected = setSelectionFromController(visualizer, startMs, endMs, selectionControllerDependencies(), options);
  if (selected) notifySelectionChanged(visualizer, options.origin ?? "user");
  syncSelectionToolbar(visualizer);
  return selected;
}

export function shiftSelectionEdgeToMarker(
  visualizer: VisualizerElement,
  edge: SelectionShiftEdge,
  direction: SelectionShiftDirection,
  options: { origin?: SelectionMutationOrigin } = {},
): boolean {
  const selection = selectionForVisualizer(visualizer);
  if (!selection) return false;
  const resolution = resolveSelectionMarkerShift(
    selection,
    edge,
    direction,
    chorusingStateForVisualizer(visualizer).markersMs,
    readVisualizerTargetDurationMs(visualizer),
  );
  if (!resolution.nextRange) return false;
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const previousPlaybackState = playbackStateFor(visualizer);
  if (previousPlaybackState === "playing") {
    stopProgressClock(visualizer, { clearEngine: false });
  }
  const shifted = setSelection(
    visualizer,
    resolution.nextRange.startMs,
    resolution.nextRange.endMs,
    { origin: options.origin ?? "user" },
  );
  if (!shifted) return false;
  if (previousPlaybackState === "paused") {
    setVisualizerResumeRequiresRestart(visualizer, true);
  }
  if (previousPlaybackState === "playing" && audioClockReady(visualizer)) {
    startEditorHtmlPlayback(
      visualizer,
      playbackRequestForStart(visualizer, ord, resolution.nextRange.startMs, "html"),
    );
  }
  return true;
}

export function shiftSelectionEdgeToMarkerForOrd(
  ord: number,
  edge: SelectionShiftEdge,
  direction: SelectionShiftDirection,
): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  return shiftSelectionEdgeToMarker(visualizer, edge, direction);
}

export function shouldTreatSelectionGestureAsClick(
  startEvent: Pick<PointerEvent, "clientX">,
  endEvent: Pick<PointerEvent, "clientX">,
  startMs: number,
  endMs: number,
): boolean {
  return isClickLikeSelectionGesture(startEvent, endEvent, startMs, endMs);
}

function selectionGestureDependencies(): SelectionGestureDependencies {
  return {
    audioClockReady,
    clearSelection,
    clearSelectionDraft,
    commitSelectionDraft,
    currentProgressMs,
    draftSelectionForVisualizer,
    playbackRequestForStart,
    playbackStateFor,
    seekAudioClock,
    selectionForVisualizer,
    setCursor,
    setSelection,
    setSelectionDraft,
    startEditorHtmlPlayback,
    stopProgressClock,
    visualizerForOrd,
  };
}

function selectionControllerDependencies(): SelectionControllerDependencies {
  return {
    setCursor,
  };
}

export function startCursorDrag(event: PointerEvent, visualizer: VisualizerElement, ord: number, notifyPython: boolean): void {
  startCursorDragGesture(event, visualizer, ord, notifyPython, selectionGestureDependencies());
}

export function startSelectionGesture(event: PointerEvent, visualizer: VisualizerElement, ord: number): void {
  startSelectionGestureFlow(event, visualizer, ord, selectionGestureDependencies());
}

export function startSelectionResizeGesture(
  event: PointerEvent,
  ord: number,
  edge: SelectionResizeEdge,
): void {
  visualizerForOrd(ord)?.focus();
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  startSelectionResizeGestureFlow(event, visualizer, ord, edge, selectionGestureDependencies());
}

export function handleVisualizerPointerDown(event: PointerEvent, ord: number): void {
  visualizerForOrd(ord)?.focus();
  handleVisualizerPointerDownGesture(event, ord, selectionGestureDependencies());
}
