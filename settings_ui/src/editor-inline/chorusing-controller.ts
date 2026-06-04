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
import { setSelection as setSelectionFromController } from "./selection-controller.js";
import { SELECTION_CHANGED_EVENT, notifySelectionChanged, type SelectionChangedDetail } from "./selection-events.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import {
  renderChorusingMarkerRow,
  chorusingStateForVisualizer,
  writeChorusingState,
} from "./chorusing-dom.js";
import { syncChorusingToolbarButtons } from "./chorusing-toolbar.js";
import {
  activeMarkerIndexAfterMarkerToggle,
  chooseInitialActiveMarkerIndex,
  defaultChorusingMarkers,
  deriveActiveSuffix,
  emptyChorusingState,
  moveActiveMarkerIndex,
  type ChorusingMarkerDirection,
  type ChorusingState,
  toggleChorusingMarker,
} from "./chorusing-state";
import {
  readVisualizerCursorMs,
  readVisualizerTargetDurationMs,
  readVisualizerTimeViewport,
} from "./visualizer-state.js";

const MARKER_HIT_TOLERANCE_MS = 35;

export function installChorusingHandlers(visualizer: VisualizerElement): () => void {
  writeState(visualizer, chorusingStateForVisualizer(visualizer));
  const onSelectionChanged = (event: Event): void => {
    const origin = (event as CustomEvent<SelectionChangedDetail>).detail?.origin ?? "user";
    if (origin === "user") {
      renderChorusingMarkerRow(visualizer);
      syncChorusingToolbarButtons(visualizer);
    } else {
      renderChorusingMarkerRow(visualizer);
    }
  };
  const onViewportChanged = (): void => renderChorusingMarkerRow(visualizer);
  const observer = new MutationObserver(() => {
    const state = chorusingStateForVisualizer(visualizer);
    if (visualizer.dataset.hasTrack !== "true" && state.baseRegion) {
      clearChorusing(visualizer, { restoreRepeat: true });
      return;
    }
    if (visualizer.dataset.hasTrack !== "true") return;
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

function ensureCurrentTrackChorusingBase(visualizer: VisualizerElement, state: ChorusingState): void {
  const sourceFilename = visualizer.dataset.sourceFilename || "";
  let currentState = state;
  if (state.sourceFilename && state.sourceFilename !== sourceFilename) {
    clearChorusing(visualizer, { restoreRepeat: true });
    currentState = chorusingStateForVisualizer(visualizer);
  }
  if (ensureChorusingBase(visualizer, currentState) === null) {
    writeState(visualizer, emptyChorusingState());
  }
}

export function toggleChorusingForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? toggleChorusing(visualizer) : false;
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
  const readyState = ensureChorusingBase(visualizer, state);
  if (!readyState?.baseRegion) return;
  event.preventDefault();
  event.stopPropagation();
  const click = markerClickFromEvent(event, svg, readVisualizerTimeViewport(visualizer), readyState.baseRegion);
  if (!click.insideVisibleBaseRegion) return;
  const previousSuffix = deriveActiveSuffix(
    readyState.baseRegion,
    readyState.markersMs,
    readyState.activeMarkerIndex,
  );
  const toggled = toggleChorusingMarker(
    readyState.markersMs,
    click.ms,
    readyState.baseRegion,
    MARKER_HIT_TOLERANCE_MS,
  );
  const activeMarkerIndex = activeMarkerIndexAfterMarkerToggle(
    readyState.markersMs,
    toggled.markersMs,
    readyState.activeMarkerIndex,
  );
  const nextState = {
    ...readyState,
    activeMarkerIndex,
    markersMs: toggled.markersMs,
    practiceState: toggled.markersMs.length ? readyState.practiceState : "stopped",
  };
  const nextSuffix = deriveActiveSuffix(nextState.baseRegion, nextState.markersMs, nextState.activeMarkerIndex);
  writeState(visualizer, nextState);
  if (readyState.practiceState !== "playing") return;
  if (!nextSuffix) {
    stopProgressClock(visualizer);
    focusAndSendCommand(Number(visualizer.dataset.aqeFieldOrd || "0"), "aqe:stop-playback");
    restoreOrdinaryRepeat(visualizer, readyState);
    return;
  }
  if (previousSuffix?.startMs !== nextSuffix.startMs || previousSuffix?.endMs !== nextSuffix.endMs) {
    startPracticePlayback(visualizer, nextState);
  }
}

export function pauseChorusingForNormalPlay(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  const state = chorusingStateForVisualizer(visualizer);
  if (state.practiceState !== "playing") return false;
  pauseChorusing(visualizer, state);
  return true;
}

export function clearChorusing(
  visualizer: VisualizerElement,
  options: { restoreRepeat?: boolean } = {},
): void {
  const state = chorusingStateForVisualizer(visualizer);
  if (state.practiceState !== "stopped") {
    stopProgressClock(visualizer);
    focusAndSendCommand(Number(visualizer.dataset.aqeFieldOrd || "0"), "aqe:stop-playback");
  }
  if (options.restoreRepeat !== false) restoreOrdinaryRepeat(visualizer, state);
  writeState(visualizer, emptyChorusingState());
  syncSelectionToolbar(visualizer);
}

function ensureChorusingBase(
  visualizer: VisualizerElement,
  state: ChorusingState,
): ChorusingState | null {
  const baseRegion = state.baseRegion ?? wholeFileChorusingRegion(visualizer);
  if (!baseRegion) return null;
  const newBaseRegion = state.baseRegion === null;
  const markersMs = newBaseRegion ? defaultChorusingMarkers(baseRegion) : state.markersMs;
  const nextState = {
    ...state,
    activeMarkerIndex: newBaseRegion ? chooseInitialActiveMarkerIndex(markersMs) : state.activeMarkerIndex,
    baseRegion,
    markersMs,
    sourceFilename: visualizer.dataset.sourceFilename || "",
  };
  if (newBaseRegion || state.sourceFilename !== nextState.sourceFilename) {
    writeState(visualizer, nextState);
  }
  return nextState;
}

function wholeFileChorusingRegion(visualizer: VisualizerElement) {
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  if (visualizer.dataset.hasTrack !== "true" || durationMs <= 0) return null;
  return {
    endMs: durationMs,
    mode: "selection" as const,
    startMs: 0,
  };
}

function toggleChorusing(visualizer: VisualizerElement): boolean {
  const state = chorusingStateForVisualizer(visualizer);
  if (state.practiceState === "playing") {
    pauseChorusing(visualizer, state);
    return true;
  }
  const readyState = ensurePracticeReady(visualizer, state);
  if (!readyState) return false;
  startPracticePlayback(visualizer, readyState);
  return true;
}

function moveChorusing(visualizer: VisualizerElement, direction: ChorusingMarkerDirection): boolean {
  const state = chorusingStateForVisualizer(visualizer);
  if (!state.baseRegion || !state.markersMs.length) return false;
  const nextIndex = moveActiveMarkerIndex(state.markersMs, state.activeMarkerIndex, direction);
  const nextState = {
    ...state,
    activeMarkerIndex: nextIndex,
  };
  writeState(visualizer, nextState);
  setSelectionToActiveSuffix(visualizer, nextState);
  if (nextState.practiceState === "playing") {
    startPracticePlayback(visualizer, nextState);
  }
  return true;
}

function ensurePracticeReady(
  visualizer: VisualizerElement,
  state: ChorusingState,
): ChorusingState | null {
  const baseState = ensureChorusingBase(visualizer, state);
  if (!baseState?.baseRegion || !baseState.markersMs.length) return null;
  const activeMarkerIndex = baseState.activeMarkerIndex ?? chooseInitialActiveMarkerIndex(baseState.markersMs);
  if (activeMarkerIndex === null) return null;
  const readyState = {
    ...baseState,
    activeMarkerIndex,
    ordinaryRepeatEnabled: baseState.ordinaryRepeatEnabled ?? readOrdinaryRepeat(visualizer),
    sourceFilename: visualizer.dataset.sourceFilename || "",
  };
  writeState(visualizer, readyState);
  return readyState;
}

function startPracticePlayback(visualizer: VisualizerElement, state: ChorusingState): void {
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
    source: "chorusing",
  };
  writeState(visualizer, {
    ...state,
    practiceState: "playing",
  });
  if (request.engine === "html") {
    startEditorHtmlPlayback(visualizer, request);
  } else {
    sendPlaybackRequest(request);
  }
}

function pauseChorusing(visualizer: VisualizerElement, state: ChorusingState): void {
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
    source: "chorusing",
  });
  restoreOrdinaryRepeat(visualizer, state);
  writeState(visualizer, {
    ...state,
    practiceState: "paused",
  });
}

function setSelectionToActiveSuffix(visualizer: VisualizerElement, state: ChorusingState) {
  const suffix = deriveActiveSuffix(state.baseRegion, state.markersMs, state.activeMarkerIndex);
  if (!suffix) return null;
  setSelectionFromController(visualizer, suffix.startMs, suffix.endMs, { setCursor: () => undefined }, { updateCursor: false });
  syncSelectionToolbar(visualizer);
  notifySelectionChanged(visualizer, "chorusing");
  return suffix;
}

function readOrdinaryRepeat(visualizer: VisualizerElement): boolean {
  return visualizer.dataset.repeatEnabled === "true";
}

function writeRepeatForPractice(visualizer: VisualizerElement, enabled: boolean): void {
  visualizer.dataset.repeatEnabled = enabled ? "true" : "false";
  visualizer.dataset.playbackLoop = enabled ? "true" : "false";
}

function restoreOrdinaryRepeat(visualizer: VisualizerElement, state: ChorusingState): void {
  if (state.ordinaryRepeatEnabled === null) return;
  writeRepeatForPractice(visualizer, state.ordinaryRepeatEnabled);
}

function writeState(visualizer: VisualizerElement, state: ChorusingState): void {
  writeChorusingState(visualizer, state);
  syncChorusingToolbarButtons(visualizer);
}
