import { visualizerForOrd } from "./dom-selectors.js";
import { focusAndSendCommand } from "./bridge.js";
import { markerClickFromEvent } from "./graph-overlay-geometry.js";
import {
  playbackEngineFor,
  pauseProgressClock,
  sendPlaybackRequest,
  startEditorHtmlPlayback,
  stopProgressClock,
} from "./playback-actions.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";
import { selectionForVisualizer, setSelection as setSelectionFromController } from "./selection-controller.js";
import { SELECTION_CHANGED_EVENT, notifySelectionChanged, type SelectionChangedDetail } from "./selection-events.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import {
  renderSegmentMarkerRow,
  segmentPracticeControlsForVisualizer,
  segmentPracticeStateForVisualizer,
  writeSegmentPracticeState,
  type SegmentPracticeControlsState,
} from "./segment-practice-dom.js";
import {
  chooseInitialActiveMarkerIndex,
  deriveActiveSuffix,
  emptySegmentPracticeState,
  moveActiveMarkerIndex,
  type SegmentMarkerDirection,
  type SegmentPracticeState,
  toggleSegmentMarker,
} from "./segment-practice-state.js";
import {
  readVisualizerCursorMs,
  readVisualizerTimeViewport,
} from "./visualizer-state.js";

const MARKER_HIT_TOLERANCE_MS = 35;

export function installSegmentPracticeHandlers(visualizer: VisualizerElement): () => void {
  writeSegmentPracticeState(visualizer, segmentPracticeStateForVisualizer(visualizer));
  const onSelectionChanged = (event: Event): void => {
    const origin = (event as CustomEvent<SelectionChangedDetail>).detail?.origin ?? "user";
    if (origin === "user") {
      clearSegmentPractice(visualizer, { restoreRepeat: true });
    } else {
      renderSegmentMarkerRow(visualizer);
    }
  };
  const onViewportChanged = (): void => renderSegmentMarkerRow(visualizer);
  const observer = new MutationObserver(() => {
    const state = segmentPracticeStateForVisualizer(visualizer);
    if (!state.sourceFilename || state.sourceFilename === (visualizer.dataset.sourceFilename || "")) return;
    clearSegmentPractice(visualizer, { restoreRepeat: true });
  });
  visualizer.addEventListener(SELECTION_CHANGED_EVENT, onSelectionChanged);
  visualizer.addEventListener("aqe-viewport-rendered", onViewportChanged);
  observer.observe(visualizer, {
    attributeFilter: ["data-source-filename", "data-has-track", "hidden"],
    attributes: true,
  });
  renderSegmentMarkerRow(visualizer);
  return () => {
    observer.disconnect();
    visualizer.removeEventListener(SELECTION_CHANGED_EVENT, onSelectionChanged);
    visualizer.removeEventListener("aqe-viewport-rendered", onViewportChanged);
  };
}

export function segmentPracticeControlsForOrd(ord: number): SegmentPracticeControlsState {
  const visualizer = visualizerForOrd(ord);
  return segmentPracticeControlsForVisualizer(visualizer);
}

export function enterSegmentPracticeForOrd(ord: number): boolean {
  return toggleSegmentPracticePanelForOrd(ord);
}

export function toggleSegmentPracticePanelForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  if (visualizer.dataset.segmentPanelOpen === "true") {
    visualizer.dataset.segmentPanelOpen = "false";
    syncSelectionToolbar(visualizer);
    return true;
  }
  const entered = setSegmentEditing(visualizer, true);
  if (!entered) return false;
  visualizer.dataset.segmentPanelOpen = "true";
  syncSelectionToolbar(visualizer);
  return true;
}

export function startSegmentEditingForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const state = segmentPracticeStateForVisualizer(visualizer);
  return setSegmentEditing(visualizer, !state.editing);
}

export function toggleSegmentPracticeForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? toggleSegmentPractice(visualizer) : false;
}

export function moveSegmentPracticeForOrd(ord: number, direction: SegmentMarkerDirection): boolean {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? moveSegmentPractice(visualizer, direction) : false;
}

export function clearSegmentPracticeForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  clearSegmentPractice(visualizer, { restoreRepeat: true });
  return true;
}

export function clearSegmentMarkersForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  clearSegmentMarkers(visualizer);
  return true;
}

export function handleSegmentMarkerPointerDown(event: PointerEvent, ord: number): void {
  const visualizer = visualizerForOrd(ord);
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  const state = visualizer ? segmentPracticeStateForVisualizer(visualizer) : null;
  if (!visualizer || !svg || !state?.baseRegion || !state.editing) return;
  event.preventDefault();
  event.stopPropagation();
  const click = markerClickFromEvent(event, svg, readVisualizerTimeViewport(visualizer), state.baseRegion);
  if (!click.insideVisibleBaseRegion) return;
  const toggled = toggleSegmentMarker(state.markersMs, click.ms, state.baseRegion, MARKER_HIT_TOLERANCE_MS);
  const activeMarkerIndex = state.practiceState === "stopped" || state.activeMarkerIndex === null
    ? chooseInitialActiveMarkerIndex(toggled.markersMs)
    : Math.min(state.activeMarkerIndex, Math.max(0, toggled.markersMs.length - 1));
  writeSegmentPracticeState(visualizer, {
    ...state,
    activeMarkerIndex: toggled.markersMs.length ? activeMarkerIndex : null,
    markersMs: toggled.markersMs,
  });
}

export function pauseSegmentPracticeForNormalPlay(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const state = segmentPracticeStateForVisualizer(visualizer);
  if (state.practiceState !== "playing") return false;
  pauseSegmentPractice(visualizer, state);
  return true;
}

export function clearSegmentPractice(
  visualizer: VisualizerElement,
  options: { restoreRepeat?: boolean } = {},
): void {
  const state = segmentPracticeStateForVisualizer(visualizer);
  if (state.practiceState !== "stopped") {
    stopProgressClock(visualizer);
    focusAndSendCommand(Number(visualizer.dataset.aqeFieldOrd || "0"), "aqe:stop-playback");
  }
  if (options.restoreRepeat !== false) restoreOrdinaryRepeat(visualizer, state);
  visualizer.dataset.segmentPanelOpen = "false";
  writeSegmentPracticeState(visualizer, emptySegmentPracticeState());
  syncSelectionToolbar(visualizer);
}

function setSegmentEditing(visualizer: VisualizerElement, editing: boolean): boolean {
  const state = segmentPracticeStateForVisualizer(visualizer);
  const baseRegion = state.baseRegion ?? selectionForVisualizer(visualizer);
  if (!baseRegion) return false;
  writeSegmentPracticeState(visualizer, {
    ...state,
    activeMarkerIndex: state.baseRegion ? state.activeMarkerIndex : null,
    baseRegion,
    editing,
    markersMs: state.baseRegion ? state.markersMs : [],
    sourceFilename: visualizer.dataset.sourceFilename || "",
  });
  return true;
}

function toggleSegmentPractice(visualizer: VisualizerElement): boolean {
  const state = segmentPracticeStateForVisualizer(visualizer);
  if (state.practiceState === "playing") {
    pauseSegmentPractice(visualizer, state);
    return true;
  }
  const readyState = ensurePracticeReady(visualizer, state);
  if (!readyState) return false;
  startPracticePlayback(visualizer, readyState);
  return true;
}

function moveSegmentPractice(visualizer: VisualizerElement, direction: SegmentMarkerDirection): boolean {
  const state = segmentPracticeStateForVisualizer(visualizer);
  if (!state.baseRegion || !state.markersMs.length) return false;
  const nextIndex = moveActiveMarkerIndex(state.markersMs, state.activeMarkerIndex, direction);
  const nextState = {
    ...state,
    activeMarkerIndex: nextIndex,
  };
  writeSegmentPracticeState(visualizer, nextState);
  setSelectionToActiveSuffix(visualizer, nextState);
  if (nextState.practiceState === "playing") {
    startPracticePlayback(visualizer, nextState);
  }
  return true;
}

function ensurePracticeReady(
  visualizer: VisualizerElement,
  state: SegmentPracticeState,
): SegmentPracticeState | null {
  const baseRegion = state.baseRegion ?? selectionForVisualizer(visualizer);
  if (!baseRegion || !state.markersMs.length) return null;
  const activeMarkerIndex = state.activeMarkerIndex ?? chooseInitialActiveMarkerIndex(state.markersMs);
  if (activeMarkerIndex === null) return null;
  const readyState = {
    ...state,
    activeMarkerIndex,
    baseRegion,
    editing: state.editing,
    ordinaryRepeatEnabled: state.ordinaryRepeatEnabled ?? readOrdinaryRepeat(visualizer),
    sourceFilename: visualizer.dataset.sourceFilename || "",
  };
  writeSegmentPracticeState(visualizer, readyState);
  return readyState;
}

function startPracticePlayback(visualizer: VisualizerElement, state: SegmentPracticeState): void {
  const suffix = setSelectionToActiveSuffix(visualizer, state);
  if (!suffix) return;
  stopProgressClock(visualizer, { clearEngine: false });
  writeRepeatForPractice(visualizer, true);
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const request: PlaybackRequest = {
    action: "start",
    cursorMs: Math.round(suffix.startMs),
    endMs: Math.round(suffix.endMs),
    engine: playbackEngineFor(visualizer),
    loop: true,
    ord,
    regionMode: "selection",
  };
  writeSegmentPracticeState(visualizer, {
    ...state,
    practiceState: "playing",
  });
  if (request.engine === "html") {
    startEditorHtmlPlayback(visualizer, request);
  } else {
    sendPlaybackRequest(request);
  }
}

function pauseSegmentPractice(visualizer: VisualizerElement, state: SegmentPracticeState): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  pauseProgressClock(visualizer);
  sendPlaybackRequest({
    action: "pause",
    cursorMs: readVisualizerCursorMs(visualizer),
    engine: visualizer.dataset.playbackEngine === "html" || visualizer.dataset.playbackEngine === "native"
      ? visualizer.dataset.playbackEngine
      : playbackEngineFor(visualizer),
    loop: true,
    ord,
    regionMode: "selection",
  });
  restoreOrdinaryRepeat(visualizer, state);
  writeSegmentPracticeState(visualizer, {
    ...state,
    practiceState: "paused",
  });
}

function clearSegmentMarkers(visualizer: VisualizerElement): void {
  const state = segmentPracticeStateForVisualizer(visualizer);
  if (state.practiceState !== "stopped") {
    stopProgressClock(visualizer);
    focusAndSendCommand(Number(visualizer.dataset.aqeFieldOrd || "0"), "aqe:stop-playback");
  }
  restoreOrdinaryRepeat(visualizer, state);
  const baseRegion = state.baseRegion ?? selectionForVisualizer(visualizer);
  if (!baseRegion) {
    writeSegmentPracticeState(visualizer, emptySegmentPracticeState());
    return;
  }
  writeSegmentPracticeState(visualizer, {
    ...state,
    activeMarkerIndex: null,
    baseRegion,
    editing: true,
    markersMs: [],
    ordinaryRepeatEnabled: null,
    practiceState: "stopped",
    sourceFilename: visualizer.dataset.sourceFilename || "",
  });
}

function setSelectionToActiveSuffix(visualizer: VisualizerElement, state: SegmentPracticeState) {
  const suffix = deriveActiveSuffix(state.baseRegion, state.markersMs, state.activeMarkerIndex);
  if (!suffix) return null;
  setSelectionFromController(visualizer, suffix.startMs, suffix.endMs, { setCursor: () => undefined }, { updateCursor: false });
  syncSelectionToolbar(visualizer);
  notifySelectionChanged(visualizer, "segment-practice");
  return suffix;
}

function readOrdinaryRepeat(visualizer: VisualizerElement): boolean {
  return visualizer.dataset.repeatEnabled === "true";
}

function writeRepeatForPractice(visualizer: VisualizerElement, enabled: boolean): void {
  visualizer.dataset.repeatEnabled = enabled ? "true" : "false";
  visualizer.dataset.playbackLoop = enabled ? "true" : "false";
}

function restoreOrdinaryRepeat(visualizer: VisualizerElement, state: SegmentPracticeState): void {
  if (state.ordinaryRepeatEnabled === null) return;
  writeRepeatForPractice(visualizer, state.ordinaryRepeatEnabled);
}
