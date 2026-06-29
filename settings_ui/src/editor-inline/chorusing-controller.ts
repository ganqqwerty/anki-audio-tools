import { markerClickFromEvent } from "./graph-overlay-geometry.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { readFieldState } from "./field-state-store.js";
import { selectionForVisualizer, setSelection as setSelectionFromController } from "./selection-controller.js";
import { SELECTION_CHANGED_EVENT, notifySelectionChanged } from "./selection-events.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import { startSourcePlaybackAction } from "./source-playback-actions.js";
import {
  chorusingMarkerControlsVisible,
  chorusingStateForVisualizer,
  renderChorusingMarkerRow,
  writeChorusingState,
} from "./chorusing-dom.js";
import { syncChorusingToolbarButtons } from "./chorusing-toolbar.js";
import { splitButtonDefaults } from "./split-button-state.js";
import {
  clampChorusingMarkerIntervalMs,
  defaultChorusingMarkers,
  emptyChorusingState,
  markerIndexForExactStart,
  moveActiveMarkerIndexForSuffix,
  toggleChorusingMarker,
  type ChorusingMarkerDirection,
  type ChorusingState,
} from "./chorusing-state";
import type { PlaybackRegion } from "./playback-model.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";
import {
  readVisualizerTargetDurationMs,
  readVisualizerTimeViewport,
} from "./visualizer-state.js";

const MARKER_HIT_TOLERANCE_MS = 35;

export function installChorusingHandlers(visualizer: VisualizerElement): () => void {
  writeState(visualizer, chorusingStateForVisualizer(visualizer));
  const onSelectionChanged = (event: Event): void => {
    const origin = event instanceof CustomEvent ? (event.detail?.origin ?? "user") : "user";
    if (origin === "user") {
      scheduleUserSelectionChorusingSync(visualizer);
    }
    renderChorusingMarkerRow(visualizer);
    syncChorusingToolbarButtons(visualizer);
  };
  const onViewportChanged = (): void => renderChorusingMarkerRow(visualizer);
  const observer = new MutationObserver(() => {
    const state = chorusingStateForVisualizer(visualizer);
    const fieldState = readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"));
    if (!fieldState.graph.hasTrack && state.baseRegion) {
      clearChorusing(visualizer);
      return;
    }
    if (!fieldState.graph.hasTrack) return;
    ensureCurrentTrackChorusingBase(visualizer, state);
  });
  visualizer.addEventListener(SELECTION_CHANGED_EVENT, onSelectionChanged);
  visualizer.addEventListener("aqe-viewport-rendered", onViewportChanged);
  observer.observe(visualizer, {
    attributeFilter: ["data-source-filename", "data-has-track", "hidden"],
    attributes: true,
  });
  ensureCurrentTrackChorusingBase(visualizer, chorusingStateForVisualizer(visualizer));
  return () => {
    observer.disconnect();
    visualizer.removeEventListener(SELECTION_CHANGED_EVENT, onSelectionChanged);
    visualizer.removeEventListener("aqe-viewport-rendered", onViewportChanged);
  };
}

export function moveChorusingForOrd(ord: number, direction: ChorusingMarkerDirection): boolean {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? moveChorusing(visualizer, direction) : false;
}

export function handleChorusingMarkerPointerDown(event: PointerEvent, ord: number): void {
  const visualizer = visualizerForOrd(ord);
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  const state = visualizer ? chorusingStateForVisualizer(visualizer) : null;
  if (!visualizer || !svg || !state) return;
  if (!chorusingMarkerControlsVisible(visualizer)) return;
  const readyState = ensureChorusingBase(visualizer, state);
  if (!readyState?.baseRegion) return;
  event.preventDefault();
  event.stopPropagation();
  const click = markerClickFromEvent(event, svg, readVisualizerTimeViewport(visualizer), readyState.baseRegion);
  if (!click.insideVisibleBaseRegion) return;
  const toggled = toggleChorusingMarker(
    readyState.markersMs,
    click.ms,
    readyState.baseRegion,
    MARKER_HIT_TOLERANCE_MS,
  );
  writeState(visualizer, {
    ...readyState,
    markersMs: toggled.markersMs,
  });
}

export function clearChorusing(visualizer: VisualizerElement): void {
  writeState(visualizer, emptyChorusingState());
  syncSelectionToolbar(visualizer);
}

function ensureCurrentTrackChorusingBase(visualizer: VisualizerElement, state: ChorusingState): void {
  const sourceFilename = readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0")).sourceFilename;
  let currentState = state;
  if (state.sourceFilename && state.sourceFilename !== sourceFilename) {
    clearChorusing(visualizer);
    currentState = chorusingStateForVisualizer(visualizer);
  }
  if (ensureChorusingBase(visualizer, currentState) === null) {
    writeState(visualizer, emptyChorusingState());
  }
}

function ensureChorusingBase(
  visualizer: VisualizerElement,
  state: ChorusingState,
): ChorusingState | null {
  const baseRegion = state.baseRegion ?? wholeFileChorusingRegion(visualizer);
  if (!baseRegion) return null;
  const newBaseRegion = state.baseRegion === null;
  const markersMs = newBaseRegion
    ? defaultChorusingMarkers(baseRegion, chorusingMarkerIntervalMs())
    : state.markersMs;
  const nextState = {
    ...state,
    baseRegion,
    markersMs,
    sourceFilename: readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0")).sourceFilename,
  };
  if (newBaseRegion || state.sourceFilename !== nextState.sourceFilename) {
    writeState(visualizer, nextState);
  }
  return nextState;
}

function chorusingMarkerIntervalMs(): number {
  return clampChorusingMarkerIntervalMs(splitButtonDefaults().chorusingMarkerIntervalMs);
}

function wholeFileChorusingRegion(visualizer: VisualizerElement): PlaybackRegion | null {
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  if (!readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0")).graph.hasTrack || durationMs <= 0) return null;
  return {
    endMs: durationMs,
    mode: "selection",
    startMs: 0,
  };
}

function moveChorusing(
  visualizer: VisualizerElement,
  direction: ChorusingMarkerDirection,
  options: { resetRepeatPasses?: boolean } = {},
): boolean {
  const readyState = ensureChorusingBase(visualizer, chorusingStateForVisualizer(visualizer));
  if (!readyState?.baseRegion || !readyState.markersMs.length) return false;
  const selection = activeMarkerSelection(readyState, selectionForVisualizer(visualizer));
  const nextSelection = selection
    ? selectionAfterMarkerNavigation(selection, readyState.markersMs, direction, readyState.baseRegion.endMs)
    : rightmostSuffixSelection(readyState);
  if (!nextSelection) return false;
  writeState(visualizer, {
    ...readyState,
    fullBaseSelectionActive: isBaseSelection(readyState, nextSelection),
    repeatPassesCompleted: options.resetRepeatPasses === false ? readyState.repeatPassesCompleted : 0,
  });
  setSelectedSuffix(visualizer, nextSelection);
  restartSelectedPlaybackIfPlaying(visualizer, nextSelection);
  return true;
}

function scheduleUserSelectionChorusingSync(visualizer: VisualizerElement): void {
  queueMicrotask(() => {
    const state = chorusingStateForVisualizer(visualizer);
    writeState(visualizer, {
      ...state,
      fullBaseSelectionActive: false,
      repeatPassesCompleted: 0,
    });
    const selection = activeMarkerSelection(state, selectionForVisualizer(visualizer));
    if (selection) {
      restartSelectedPlaybackIfPlaying(visualizer, selection);
    }
  });
}

function rightmostSuffixSelection(state: ChorusingState): { startMs: number; endMs: number } | null {
  if (!state.baseRegion || !state.markersMs.length) return null;
  const startMs = state.markersMs[state.markersMs.length - 1];
  if (typeof startMs !== "number" || !Number.isFinite(startMs)) return null;
  return {
    endMs: state.baseRegion.endMs,
    startMs,
  };
}

function activeMarkerSelection(
  state: ChorusingState,
  selection: PlaybackRegion | null,
): PlaybackRegion | null {
  if (!selection || !state.baseRegion) return selection;
  const coversBase = Math.round(selection.startMs) <= Math.round(state.baseRegion.startMs)
    && Math.round(selection.endMs) >= Math.round(state.baseRegion.endMs);
  return coversBase && !state.fullBaseSelectionActive ? null : selection;
}

function isBaseSelection(
  state: ChorusingState,
  selection: { startMs: number; endMs: number },
): boolean {
  return Boolean(
    state.baseRegion
    && Math.round(selection.startMs) <= Math.round(state.baseRegion.startMs)
    && Math.round(selection.endMs) >= Math.round(state.baseRegion.endMs),
  );
}

function selectionAfterMarkerNavigation(
  selection: { startMs: number; endMs: number },
  markersMs: readonly number[],
  direction: ChorusingMarkerDirection,
  durationMs: number,
): { startMs: number; endMs: number } | null {
  const targetIndex = moveActiveMarkerIndexForSuffix(
    markersMs,
    markerIndexForExactStart(markersMs, selection.startMs),
    direction,
    selection.startMs,
    selection.endMs,
  );
  const startMs = targetIndex === null ? null : markersMs[targetIndex];
  if (typeof startMs !== "number" || !Number.isFinite(startMs)) return null;
  const endMs = Math.min(selection.endMs, durationMs);
  if (Math.round(startMs) >= Math.round(endMs)) return null;
  return { startMs, endMs };
}

function setSelectedSuffix(
  visualizer: VisualizerElement,
  selection: { startMs: number; endMs: number },
): void {
  setSelectionFromController(
    visualizer,
    selection.startMs,
    selection.endMs,
    { setCursor: () => undefined },
    { updateCursor: false },
  );
  syncSelectionToolbar(visualizer);
  notifySelectionChanged(visualizer, "chorusing");
}

function restartSelectedPlaybackIfPlaying(
  visualizer: VisualizerElement,
  selection: { startMs: number; endMs: number },
): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const fieldState = readFieldState(ord);
  if (fieldState.playback.state !== "playing") return;
  const request: PlaybackRequest = {
    action: "start",
    cursorMs: Math.round(selection.startMs),
    endMs: Math.round(selection.endMs),
    engine: "html",
    loop: fieldState.playback.repeat,
    ord,
    regionMode: "selection",
    source: "user",
  };
  startSourcePlaybackAction(visualizer, request);
}

function writeState(visualizer: VisualizerElement, state: ChorusingState): void {
  writeChorusingState(visualizer, state);
  syncChorusingToolbarButtons(visualizer);
}
