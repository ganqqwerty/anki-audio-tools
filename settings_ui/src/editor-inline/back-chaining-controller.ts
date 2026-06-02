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
  renderBackChainingMarkerRow,
  backChainingControlsForVisualizer,
  backChainingStateForVisualizer,
  writeBackChainingState,
  type BackChainingControlsState,
} from "./back-chaining-dom.js";
import {
  chooseInitialActiveMarkerIndex,
  defaultBackChainingMarkers,
  deriveActiveSuffix,
  emptyBackChainingState,
  moveActiveMarkerIndex,
  type BackChainingMarkerDirection,
  type BackChainingState,
  toggleBackChainingMarker,
} from "./back-chaining-state.js";
import {
  readVisualizerCursorMs,
  readVisualizerTimeViewport,
} from "./visualizer-state.js";

const MARKER_HIT_TOLERANCE_MS = 35;

export function installBackChainingHandlers(visualizer: VisualizerElement): () => void {
  writeBackChainingState(visualizer, backChainingStateForVisualizer(visualizer));
  const onSelectionChanged = (event: Event): void => {
    const origin = (event as CustomEvent<SelectionChangedDetail>).detail?.origin ?? "user";
    if (origin === "user") {
      clearBackChaining(visualizer, { restoreRepeat: true });
    } else {
      renderBackChainingMarkerRow(visualizer);
    }
  };
  const onViewportChanged = (): void => renderBackChainingMarkerRow(visualizer);
  const observer = new MutationObserver(() => {
    const state = backChainingStateForVisualizer(visualizer);
    if (!state.sourceFilename || state.sourceFilename === (visualizer.dataset.sourceFilename || "")) return;
    clearBackChaining(visualizer, { restoreRepeat: true });
  });
  visualizer.addEventListener(SELECTION_CHANGED_EVENT, onSelectionChanged);
  visualizer.addEventListener("aqe-viewport-rendered", onViewportChanged);
  observer.observe(visualizer, {
    attributeFilter: ["data-source-filename", "data-has-track", "hidden"],
    attributes: true,
  });
  renderBackChainingMarkerRow(visualizer);
  return () => {
    observer.disconnect();
    visualizer.removeEventListener(SELECTION_CHANGED_EVENT, onSelectionChanged);
    visualizer.removeEventListener("aqe-viewport-rendered", onViewportChanged);
  };
}

export function backChainingControlsForOrd(ord: number): BackChainingControlsState {
  const visualizer = visualizerForOrd(ord);
  return backChainingControlsForVisualizer(visualizer);
}

export function enterBackChainingForOrd(ord: number): boolean {
  return toggleBackChainingPanelForOrd(ord);
}

export function toggleBackChainingPanelForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  if (visualizer.dataset.backChainingPanelOpen === "true") {
    visualizer.dataset.backChainingPanelOpen = "false";
    syncSelectionToolbar(visualizer);
    return true;
  }
  const entered = setBackChainingEditing(visualizer, true);
  if (!entered) return false;
  visualizer.dataset.backChainingPanelOpen = "true";
  syncSelectionToolbar(visualizer);
  return true;
}

export function startBackChainingEditingForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const state = backChainingStateForVisualizer(visualizer);
  return setBackChainingEditing(visualizer, !state.editing);
}

export function toggleBackChainingForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? toggleBackChaining(visualizer) : false;
}

export function moveBackChainingForOrd(ord: number, direction: BackChainingMarkerDirection): boolean {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? moveBackChaining(visualizer, direction) : false;
}

export function clearBackChainingForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  clearBackChaining(visualizer, { restoreRepeat: true });
  return true;
}

export function clearBackChainingMarkersForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  clearBackChainingMarkers(visualizer);
  return true;
}

export function handleBackChainingMarkerPointerDown(event: PointerEvent, ord: number): void {
  const visualizer = visualizerForOrd(ord);
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  const state = visualizer ? backChainingStateForVisualizer(visualizer) : null;
  if (!visualizer || !svg || !state?.baseRegion || !state.editing) return;
  event.preventDefault();
  event.stopPropagation();
  const click = markerClickFromEvent(event, svg, readVisualizerTimeViewport(visualizer), state.baseRegion);
  if (!click.insideVisibleBaseRegion) return;
  const toggled = toggleBackChainingMarker(state.markersMs, click.ms, state.baseRegion, MARKER_HIT_TOLERANCE_MS);
  const activeMarkerIndex = state.practiceState === "stopped" || state.activeMarkerIndex === null
    ? chooseInitialActiveMarkerIndex(toggled.markersMs)
    : Math.min(state.activeMarkerIndex, Math.max(0, toggled.markersMs.length - 1));
  writeBackChainingState(visualizer, {
    ...state,
    activeMarkerIndex: toggled.markersMs.length ? activeMarkerIndex : null,
    markersMs: toggled.markersMs,
  });
}

export function pauseBackChainingForNormalPlay(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const state = backChainingStateForVisualizer(visualizer);
  if (state.practiceState !== "playing") return false;
  pauseBackChaining(visualizer, state);
  return true;
}

export function clearBackChaining(
  visualizer: VisualizerElement,
  options: { restoreRepeat?: boolean } = {},
): void {
  const state = backChainingStateForVisualizer(visualizer);
  if (state.practiceState !== "stopped") {
    stopProgressClock(visualizer);
    focusAndSendCommand(Number(visualizer.dataset.aqeFieldOrd || "0"), "aqe:stop-playback");
  }
  if (options.restoreRepeat !== false) restoreOrdinaryRepeat(visualizer, state);
  visualizer.dataset.backChainingPanelOpen = "false";
  writeBackChainingState(visualizer, emptyBackChainingState());
  syncSelectionToolbar(visualizer);
}

function setBackChainingEditing(visualizer: VisualizerElement, editing: boolean): boolean {
  const state = backChainingStateForVisualizer(visualizer);
  const baseRegion = state.baseRegion ?? selectionForVisualizer(visualizer);
  if (!baseRegion) return false;
  const newBaseRegion = !state.baseRegion;
  const markersMs = newBaseRegion ? defaultBackChainingMarkers(baseRegion) : state.markersMs;
  writeBackChainingState(visualizer, {
    ...state,
    activeMarkerIndex: newBaseRegion ? chooseInitialActiveMarkerIndex(markersMs) : state.activeMarkerIndex,
    baseRegion,
    editing,
    markersMs,
    sourceFilename: visualizer.dataset.sourceFilename || "",
  });
  return true;
}

function toggleBackChaining(visualizer: VisualizerElement): boolean {
  const state = backChainingStateForVisualizer(visualizer);
  if (state.practiceState === "playing") {
    pauseBackChaining(visualizer, state);
    return true;
  }
  const readyState = ensurePracticeReady(visualizer, state);
  if (!readyState) return false;
  startPracticePlayback(visualizer, readyState);
  return true;
}

function moveBackChaining(visualizer: VisualizerElement, direction: BackChainingMarkerDirection): boolean {
  const state = backChainingStateForVisualizer(visualizer);
  if (!state.baseRegion || !state.markersMs.length) return false;
  const nextIndex = moveActiveMarkerIndex(state.markersMs, state.activeMarkerIndex, direction);
  const nextState = {
    ...state,
    activeMarkerIndex: nextIndex,
  };
  writeBackChainingState(visualizer, nextState);
  setSelectionToActiveSuffix(visualizer, nextState);
  if (nextState.practiceState === "playing") {
    startPracticePlayback(visualizer, nextState);
  }
  return true;
}

function ensurePracticeReady(
  visualizer: VisualizerElement,
  state: BackChainingState,
): BackChainingState | null {
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
  writeBackChainingState(visualizer, readyState);
  return readyState;
}

function startPracticePlayback(visualizer: VisualizerElement, state: BackChainingState): void {
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
    source: "back_chaining",
  };
  writeBackChainingState(visualizer, {
    ...state,
    practiceState: "playing",
  });
  if (request.engine === "html") {
    startEditorHtmlPlayback(visualizer, request);
  } else {
    sendPlaybackRequest(request);
  }
}

function pauseBackChaining(visualizer: VisualizerElement, state: BackChainingState): void {
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
    source: "back_chaining",
  });
  restoreOrdinaryRepeat(visualizer, state);
  writeBackChainingState(visualizer, {
    ...state,
    practiceState: "paused",
  });
}

function clearBackChainingMarkers(visualizer: VisualizerElement): void {
  const state = backChainingStateForVisualizer(visualizer);
  if (state.practiceState !== "stopped") {
    stopProgressClock(visualizer);
    focusAndSendCommand(Number(visualizer.dataset.aqeFieldOrd || "0"), "aqe:stop-playback");
  }
  restoreOrdinaryRepeat(visualizer, state);
  const baseRegion = state.baseRegion ?? selectionForVisualizer(visualizer);
  if (!baseRegion) {
    writeBackChainingState(visualizer, emptyBackChainingState());
    return;
  }
  writeBackChainingState(visualizer, {
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

function setSelectionToActiveSuffix(visualizer: VisualizerElement, state: BackChainingState) {
  const suffix = deriveActiveSuffix(state.baseRegion, state.markersMs, state.activeMarkerIndex);
  if (!suffix) return null;
  setSelectionFromController(visualizer, suffix.startMs, suffix.endMs, { setCursor: () => undefined }, { updateCursor: false });
  syncSelectionToolbar(visualizer);
  notifySelectionChanged(visualizer, "back-chaining");
  return suffix;
}

function readOrdinaryRepeat(visualizer: VisualizerElement): boolean {
  return visualizer.dataset.repeatEnabled === "true";
}

function writeRepeatForPractice(visualizer: VisualizerElement, enabled: boolean): void {
  visualizer.dataset.repeatEnabled = enabled ? "true" : "false";
  visualizer.dataset.playbackLoop = enabled ? "true" : "false";
}

function restoreOrdinaryRepeat(visualizer: VisualizerElement, state: BackChainingState): void {
  if (state.ordinaryRepeatEnabled === null) return;
  writeRepeatForPractice(visualizer, state.ordinaryRepeatEnabled);
}
