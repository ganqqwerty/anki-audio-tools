import { clampMsToRegion, type PlaybackRegion } from "./playback-state.js";
import { cursorMsFromEvent } from "./plot.js";
import { startGestureSession } from "./gesture-session.js";
import {
  expandSelectionRangeToPoint,
  resizeSelectionRange,
  shouldTreatSelectionGestureAsClick,
  type SelectionResizeEdge,
} from "./selection-state.js";
import type { PlaybackRequest, PlaybackState, VisualizerElement } from "./types.js";
import {
  readVisualizerCursorMs,
  readVisualizerDurationMs,
  setVisualizerResumeRequiresRestart,
} from "./visualizer-state.js";

type CursorOptions = {
  engine?: "html" | "native" | "";
  previousPlaybackState?: PlaybackState;
  restartPlayback?: boolean;
  updateAnchor?: boolean;
};

export interface SelectionGestureDependencies {
  audioClockReady: (visualizer: VisualizerElement) => boolean;
  clearSelection: (visualizer: VisualizerElement) => void;
  clearSelectionDraft: (visualizer: VisualizerElement, options?: { redraw?: boolean }) => void;
  commitSelectionDraft: (visualizer: VisualizerElement, options?: { updateCursor?: boolean }) => boolean;
  currentProgressMs: (visualizer: VisualizerElement) => number | null;
  draftSelectionForVisualizer: (visualizer: VisualizerElement | null) => PlaybackRegion | null;
  playbackRequestForStart: (
    visualizer: VisualizerElement,
    ord: number,
    startMs: number,
    engine?: "html" | "native" | "",
  ) => PlaybackRequest;
  playbackStateFor: (visualizer: VisualizerElement) => PlaybackState;
  seekAudioClock: (visualizer: VisualizerElement, ms: number) => boolean;
  selectionForVisualizer: (visualizer: VisualizerElement | null) => PlaybackRegion | null;
  setCursor: (visualizer: VisualizerElement, ms: number, notifyPython: boolean, options?: CursorOptions) => void;
  setSelection: (
    visualizer: VisualizerElement,
    startMs: number,
    endMs: number,
    options?: { updateCursor?: boolean },
  ) => boolean;
  setSelectionDraft: (
    visualizer: VisualizerElement,
    startMs: number,
    endMs: number,
    options?: { redraw?: boolean },
  ) => boolean;
  startEditorHtmlPlayback: (visualizer: VisualizerElement, request: PlaybackRequest) => boolean;
  stopProgressClock: (
    visualizer: VisualizerElement,
    options?: { clearAudio?: boolean; clearEngine?: boolean },
  ) => void;
  visualizerForOrd: (ord: number) => VisualizerElement | null;
}

export function startCursorDrag(
  event: PointerEvent,
  visualizer: VisualizerElement,
  ord: number,
  notifyPython: boolean,
  deps: SelectionGestureDependencies,
): void {
  event.preventDefault();
  const previousPlaybackState = deps.playbackStateFor(visualizer);
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const durationMs = readVisualizerDurationMs(visualizer);
  if (!svg || !durationMs) return;
  const startEvent = { clientX: event.clientX };
  const startMs = cursorMsFromEvent(event, svg, durationMs);
  if (previousPlaybackState === "playing") {
    suspendPlaybackForGesture(visualizer, previousPlaybackState, deps);
  }
  const move = (moveEvent: PointerEvent): void => {
    deps.setCursor(visualizer, scrubMsFromEvent(moveEvent, svg, durationMs, visualizer, deps), false);
  };
  const up = (upEvent: PointerEvent): void => {
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", up);
    const restartPlayback = previousPlaybackState === "playing";
    if (previousPlaybackState === "paused") {
      setVisualizerResumeRequiresRestart(visualizer, true);
    }
    const rawReleasedMs = cursorMsFromEvent(upEvent, svg, durationMs);
    const expandedSelection = clickExpandedSelection(
      startEvent,
      upEvent,
      startMs,
      rawReleasedMs,
      visualizer,
      durationMs,
      deps,
    );
    const releasedMs = expandedSelection
      ? rawReleasedMs
      : scrubMsFromEvent(upEvent, svg, durationMs, visualizer, deps);
    const restartEngine = restartPlayback && deps.audioClockReady(visualizer) ? "html" : "";
    deps.setCursor(visualizer, releasedMs, notifyPython, {
      previousPlaybackState,
      restartPlayback,
      engine: restartEngine,
    });
    if (deps.audioClockReady(visualizer)) {
      deps.seekAudioClock(visualizer, releasedMs);
    }
    if (restartPlayback && restartEngine === "html") {
      deps.startEditorHtmlPlayback(visualizer, deps.playbackRequestForStart(visualizer, ord, releasedMs, "html"));
    }
  };
  move(event);
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", up);
}

function clickExpandedSelection(
  startEvent: Pick<PointerEvent, "clientX">,
  upEvent: PointerEvent,
  startMs: number,
  releasedMs: number,
  visualizer: VisualizerElement,
  durationMs: number,
  deps: SelectionGestureDependencies,
): boolean {
  if (!shouldTreatSelectionGestureAsClick(startEvent, upEvent, startMs, releasedMs)) return false;
  const selection = deps.selectionForVisualizer(visualizer);
  if (!selection) return false;
  const expanded = expandSelectionRangeToPoint(selection, releasedMs, durationMs);
  if (!expanded) return false;
  return deps.setSelection(visualizer, expanded.startMs, expanded.endMs, { updateCursor: false });
}

export function startSelectionGesture(
  event: PointerEvent,
  visualizer: VisualizerElement,
  ord: number,
  deps: SelectionGestureDependencies,
): void {
  event.preventDefault();
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const durationMs = readVisualizerDurationMs(visualizer);
  if (!svg || !durationMs) return;
  const previousPlaybackState = deps.playbackStateFor(visualizer);
  let frozenProgressMs = deps.currentProgressMs(visualizer) ?? readVisualizerCursorMs(visualizer);
  const startEvent = { clientX: event.clientX };
  const startMs = cursorMsFromEvent(event, svg, durationMs);
  let stoppedForDrag = false;
  const stopForDrag = (): void => {
    if (stoppedForDrag || previousPlaybackState !== "playing") return;
    stoppedForDrag = true;
    frozenProgressMs = suspendPlaybackForGesture(visualizer, previousPlaybackState, deps);
  };
  startGestureSession({
    lostPointerCaptureTarget: svg,
    onCancel() {
      deps.clearSelectionDraft(visualizer);
      resumeInterruptedSelectionPlayback(
        deps,
        visualizer,
        ord,
        previousPlaybackState,
        stoppedForDrag,
        frozenProgressMs,
      );
    },
    onPointerMove(moveEvent) {
      const moveMs = cursorMsFromEvent(moveEvent, svg, durationMs);
      if (shouldTreatSelectionGestureAsClick(startEvent, moveEvent, startMs, moveMs)) {
        deps.clearSelectionDraft(visualizer);
        return;
      }
      stopForDrag();
      deps.setSelectionDraft(visualizer, startMs, moveMs);
    },
    onPointerUp(upEvent) {
      const endMs = cursorMsFromEvent(upEvent, svg, durationMs);
      if (shouldTreatSelectionGestureAsClick(startEvent, upEvent, startMs, endMs)) {
        deps.clearSelection(visualizer);
        resumeInterruptedSelectionPlayback(
          deps,
          visualizer,
          ord,
          previousPlaybackState,
          stoppedForDrag,
          frozenProgressMs,
        );
        return;
      }
      stopForDrag();
      if (!deps.draftSelectionForVisualizer(visualizer)) {
        deps.setSelectionDraft(visualizer, startMs, endMs, { redraw: false });
      }
      const selected = deps.commitSelectionDraft(visualizer);
      if (previousPlaybackState === "paused") {
        setVisualizerResumeRequiresRestart(visualizer, true);
      }
      if (selected) {
        restartCommittedSelectionPlayback(deps, visualizer, ord, previousPlaybackState, stoppedForDrag, startMs);
      }
    },
  });
}

export function startSelectionResizeGesture(
  event: PointerEvent,
  visualizer: VisualizerElement,
  ord: number,
  edge: SelectionResizeEdge,
  deps: SelectionGestureDependencies,
): void {
  event.preventDefault();
  event.stopPropagation();
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const durationMs = readVisualizerDurationMs(visualizer);
  const selection = deps.selectionForVisualizer(visualizer);
  if (!svg || !durationMs || !selection) return;
  const previousPlaybackState = deps.playbackStateFor(visualizer);
  let frozenProgressMs = deps.currentProgressMs(visualizer) ?? readVisualizerCursorMs(visualizer);
  const cursorBeforeResizeMs = readVisualizerCursorMs(visualizer);
  const captureTarget = event.currentTarget instanceof Element ? event.currentTarget : svg;
  let stoppedForDrag = false;
  let latestRange = selection;
  const stopForDrag = (): void => {
    if (stoppedForDrag || previousPlaybackState !== "playing") return;
    stoppedForDrag = true;
    frozenProgressMs = suspendPlaybackForGesture(visualizer, previousPlaybackState, deps);
  };
  const resizeFromEvent = (resizeEvent: PointerEvent): PlaybackRegion | null => {
    const edgeMs = cursorMsFromEvent(resizeEvent, svg, durationMs);
    const range = resizeSelectionRange(selection, edge, edgeMs, durationMs);
    return range ? { ...range, mode: "selection" } : null;
  };
  stopForDrag();
  startGestureSession({
    lostPointerCaptureTarget: captureTarget,
    onCancel() {
      deps.clearSelectionDraft(visualizer);
      if (edge === "start") {
        deps.setCursor(visualizer, cursorBeforeResizeMs, false, { updateAnchor: false });
      }
      resumeInterruptedSelectionPlayback(
        deps,
        visualizer,
        ord,
        previousPlaybackState,
        stoppedForDrag,
        frozenProgressMs,
      );
    },
    onPointerMove(moveEvent) {
      const resized = resizeFromEvent(moveEvent);
      if (!resized) {
        deps.clearSelectionDraft(visualizer);
        return;
      }
      latestRange = resized;
      deps.setSelectionDraft(visualizer, resized.startMs, resized.endMs);
      if (edge === "start") {
        deps.setCursor(visualizer, resized.startMs, false, { updateAnchor: false });
      }
    },
    onPointerUp(upEvent) {
      const resized = resizeFromEvent(upEvent);
      if (resized) {
        latestRange = resized;
        if (!deps.draftSelectionForVisualizer(visualizer)) {
          deps.setSelectionDraft(visualizer, resized.startMs, resized.endMs, { redraw: false });
        }
        deps.commitSelectionDraft(visualizer);
      } else {
        deps.clearSelectionDraft(visualizer);
      }
      if (previousPlaybackState === "paused") {
        setVisualizerResumeRequiresRestart(visualizer, true);
      }
      restartCommittedSelectionPlayback(
        deps,
        visualizer,
        ord,
        previousPlaybackState,
        stoppedForDrag,
        latestRange.startMs,
      );
    },
  });
}

export function handleVisualizerPointerDown(
  event: PointerEvent,
  ord: number,
  deps: SelectionGestureDependencies,
): void {
  const visualizer = deps.visualizerForOrd(ord);
  if (!visualizer) return;
  if (event.shiftKey) {
    startSelectionGesture(event, visualizer, ord, deps);
    return;
  }
  startCursorDrag(event, visualizer, ord, true, deps);
}

function scrubMsFromEvent(
  event: Pick<PointerEvent, "clientX">,
  svg: SVGSVGElement,
  durationMs: number,
  visualizer: VisualizerElement,
  deps: SelectionGestureDependencies,
): number {
  const rawMs = cursorMsFromEvent(event, svg, durationMs);
  const selection = deps.selectionForVisualizer(visualizer);
  if (selection) {
    return clampMsToRegion(rawMs, selection);
  }
  return rawMs;
}

function suspendPlaybackForGesture(
  visualizer: VisualizerElement,
  previousPlaybackState: PlaybackState,
  deps: SelectionGestureDependencies,
): number {
  const frozenProgressMs = deps.currentProgressMs(visualizer) ?? readVisualizerCursorMs(visualizer);
  if (previousPlaybackState === "playing") {
    deps.stopProgressClock(visualizer, { clearEngine: false });
    deps.setCursor(visualizer, frozenProgressMs, false, { updateAnchor: false });
  }
  return frozenProgressMs;
}

function resumeInterruptedSelectionPlayback(
  deps: SelectionGestureDependencies,
  visualizer: VisualizerElement,
  ord: number,
  previousPlaybackState: PlaybackState,
  stoppedForGesture: boolean,
  interruptedProgressMs: number,
): void {
  if (previousPlaybackState !== "playing" || !stoppedForGesture) return;
  deps.startEditorHtmlPlayback(
    visualizer,
    deps.playbackRequestForStart(visualizer, ord, interruptedProgressMs, "html"),
  );
}

function restartCommittedSelectionPlayback(
  deps: SelectionGestureDependencies,
  visualizer: VisualizerElement,
  ord: number,
  previousPlaybackState: PlaybackState,
  stoppedForGesture: boolean,
  fallbackStartMs: number,
): void {
  if (previousPlaybackState !== "playing" || !stoppedForGesture) return;
  const committedSelection = deps.selectionForVisualizer(visualizer);
  deps.startEditorHtmlPlayback(
    visualizer,
    deps.playbackRequestForStart(visualizer, ord, committedSelection?.startMs ?? fallbackStartMs, "html"),
  );
}
