import { clampMsToRegion, type PlaybackRegion } from "./playback-state.js";
import { cursorMsFromEvent } from "./plot.js";
import {
  resizeSelectionRange,
  shouldTreatSelectionGestureAsClick,
  type SelectionResizeEdge,
} from "./selection-state.js";
import type { PlaybackRequest, PlaybackState, VisualizerElement } from "./types.js";

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
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  if (!svg || !durationMs) return;
  if (previousPlaybackState === "playing") {
    deps.stopProgressClock(visualizer);
  }
  const move = (moveEvent: PointerEvent): void => {
    deps.setCursor(visualizer, scrubMsFromEvent(moveEvent, svg, durationMs, visualizer, deps), false);
  };
  const up = (upEvent: PointerEvent): void => {
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", up);
    const restartPlayback = previousPlaybackState === "playing";
    if (previousPlaybackState === "paused") {
      visualizer.dataset.resumeRequiresRestart = "true";
    }
    const releasedMs = scrubMsFromEvent(upEvent, svg, durationMs, visualizer, deps);
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

export function startSelectionGesture(
  event: PointerEvent,
  visualizer: VisualizerElement,
  ord: number,
  deps: SelectionGestureDependencies,
): void {
  event.preventDefault();
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  if (!svg || !durationMs) return;
  const previousPlaybackState = deps.playbackStateFor(visualizer);
  const frozenProgressMs = deps.currentProgressMs(visualizer) ?? Number(visualizer.dataset.cursorMs || "0");
  const startEvent = { clientX: event.clientX };
  const startMs = cursorMsFromEvent(event, svg, durationMs);
  let stoppedForDrag = false;
  let move = (_moveEvent: PointerEvent): void => {};
  let up = (_upEvent: PointerEvent): void => {};
  let cancel = (): void => {};
  let keydown = (_keyEvent: KeyboardEvent): void => {};
  const cleanup = (): void => {
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", up);
    window.removeEventListener("pointercancel", cancel);
    window.removeEventListener("keydown", keydown);
    window.removeEventListener("blur", cancel);
    svg.removeEventListener("lostpointercapture", cancel);
  };
  const stopForDrag = (): void => {
    if (stoppedForDrag || previousPlaybackState !== "playing") return;
    stoppedForDrag = true;
    deps.stopProgressClock(visualizer, { clearEngine: false });
    deps.setCursor(visualizer, frozenProgressMs, false, { updateAnchor: false });
  };
  const resumeInterruptedPlayback = (): void => {
    if (previousPlaybackState === "playing" && stoppedForDrag) {
      deps.startEditorHtmlPlayback(
        visualizer,
        deps.playbackRequestForStart(visualizer, ord, frozenProgressMs, "html"),
      );
    }
  };
  move = (moveEvent: PointerEvent): void => {
    const moveMs = cursorMsFromEvent(moveEvent, svg, durationMs);
    if (shouldTreatSelectionGestureAsClick(startEvent, moveEvent, startMs, moveMs)) {
      deps.clearSelectionDraft(visualizer);
      return;
    }
    stopForDrag();
    deps.setSelectionDraft(visualizer, startMs, moveMs);
  };
  up = (upEvent: PointerEvent): void => {
    cleanup();
    const endMs = cursorMsFromEvent(upEvent, svg, durationMs);
    if (shouldTreatSelectionGestureAsClick(startEvent, upEvent, startMs, endMs)) {
      deps.clearSelection(visualizer);
      resumeInterruptedPlayback();
      return;
    }
    stopForDrag();
    if (!deps.draftSelectionForVisualizer(visualizer)) {
      deps.setSelectionDraft(visualizer, startMs, endMs, { redraw: false });
    }
    const selected = deps.commitSelectionDraft(visualizer);
    if (previousPlaybackState === "paused") {
      visualizer.dataset.resumeRequiresRestart = "true";
    }
    if (selected && previousPlaybackState === "playing") {
      const selection = deps.selectionForVisualizer(visualizer);
      deps.startEditorHtmlPlayback(
        visualizer,
        deps.playbackRequestForStart(visualizer, ord, selection?.startMs ?? startMs, "html"),
      );
    }
  };
  cancel = (): void => {
    cleanup();
    deps.clearSelectionDraft(visualizer);
    resumeInterruptedPlayback();
  };
  keydown = (keyEvent: KeyboardEvent): void => {
    if (keyEvent.key === "Escape") {
      cancel();
    }
  };
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", up);
  window.addEventListener("pointercancel", cancel);
  window.addEventListener("keydown", keydown);
  window.addEventListener("blur", cancel);
  svg.addEventListener("lostpointercapture", cancel);
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
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const selection = deps.selectionForVisualizer(visualizer);
  if (!svg || !durationMs || !selection) return;
  const previousPlaybackState = deps.playbackStateFor(visualizer);
  const frozenProgressMs = deps.currentProgressMs(visualizer) ?? Number(visualizer.dataset.cursorMs || "0");
  const captureTarget = event.currentTarget instanceof Element ? event.currentTarget : svg;
  let stoppedForDrag = false;
  let latestRange = selection;
  let move = (_moveEvent: PointerEvent): void => {};
  let up = (_upEvent: PointerEvent): void => {};
  let cancel = (): void => {};
  let keydown = (_keyEvent: KeyboardEvent): void => {};
  const cleanup = (): void => {
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", up);
    window.removeEventListener("pointercancel", cancel);
    window.removeEventListener("keydown", keydown);
    window.removeEventListener("blur", cancel);
    captureTarget.removeEventListener("lostpointercapture", cancel);
  };
  const stopForDrag = (): void => {
    if (stoppedForDrag || previousPlaybackState !== "playing") return;
    stoppedForDrag = true;
    deps.stopProgressClock(visualizer, { clearEngine: false });
    deps.setCursor(visualizer, frozenProgressMs, false, { updateAnchor: false });
  };
  const resizeFromEvent = (resizeEvent: PointerEvent): PlaybackRegion | null => {
    const edgeMs = cursorMsFromEvent(resizeEvent, svg, durationMs);
    const range = resizeSelectionRange(selection, edge, edgeMs, durationMs);
    return range ? { ...range, mode: "selection" } : null;
  };
  const restartFromSelectionStart = (): void => {
    if (previousPlaybackState !== "playing" || !stoppedForDrag) return;
    const committedSelection = deps.selectionForVisualizer(visualizer);
    deps.startEditorHtmlPlayback(
      visualizer,
      deps.playbackRequestForStart(visualizer, ord, committedSelection?.startMs ?? latestRange.startMs, "html"),
    );
  };
  stopForDrag();
  move = (moveEvent: PointerEvent): void => {
    const resized = resizeFromEvent(moveEvent);
    if (!resized) {
      deps.clearSelectionDraft(visualizer);
      return;
    }
    latestRange = resized;
    deps.setSelectionDraft(visualizer, resized.startMs, resized.endMs);
  };
  up = (upEvent: PointerEvent): void => {
    cleanup();
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
      visualizer.dataset.resumeRequiresRestart = "true";
    }
    restartFromSelectionStart();
  };
  cancel = (): void => {
    cleanup();
    deps.clearSelectionDraft(visualizer);
    restartFromSelectionStart();
  };
  keydown = (keyEvent: KeyboardEvent): void => {
    if (keyEvent.key === "Escape") {
      cancel();
    }
  };
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", up);
  window.addEventListener("pointercancel", cancel);
  window.addEventListener("keydown", keydown);
  window.addEventListener("blur", cancel);
  captureTarget.addEventListener("lostpointercapture", cancel);
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
  if (selection && visualizer.dataset.repeatEnabled === "true") {
    return clampMsToRegion(rawMs, selection);
  }
  return rawMs;
}
