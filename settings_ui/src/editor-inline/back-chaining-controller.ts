import { buttonFor, visualizerForOrd } from "./dom-selectors.js";
import { focusAndSendCommand } from "./bridge.js";
import { t } from "../lib/i18n.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
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
  renderBackChainingMarkerRow,
  backChainingControlsForVisualizer,
  backChainingStateForVisualizer,
  writeBackChainingState,
} from "./back-chaining-dom.js";
import {
  activeMarkerIndexAfterMarkerToggle,
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
  readVisualizerTargetDurationMs,
  readVisualizerTimeViewport,
} from "./visualizer-state.js";

const MARKER_HIT_TOLERANCE_MS = 35;

export function installBackChainingHandlers(visualizer: VisualizerElement): () => void {
  writeState(visualizer, backChainingStateForVisualizer(visualizer));
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
    if (visualizer.dataset.hasTrack !== "true" && state.baseRegion) {
      clearBackChaining(visualizer, { restoreRepeat: true });
      return;
    }
    if (!state.sourceFilename || state.sourceFilename === (visualizer.dataset.sourceFilename || "")) return;
    clearBackChaining(visualizer, { restoreRepeat: true });
    syncBackChainingToolbarButtons(visualizer);
  });
  visualizer.addEventListener(SELECTION_CHANGED_EVENT, onSelectionChanged);
  visualizer.addEventListener("aqe-viewport-rendered", onViewportChanged);
  observer.observe(visualizer, {
    attributeFilter: ["data-source-filename", "data-has-track", "hidden"],
    attributes: true,
  });
  renderBackChainingMarkerRow(visualizer);
  syncBackChainingToolbarButtons(visualizer);
  return () => {
    observer.disconnect();
    visualizer.removeEventListener(SELECTION_CHANGED_EVENT, onSelectionChanged);
    visualizer.removeEventListener("aqe-viewport-rendered", onViewportChanged);
  };
}

export function toggleBackChainingForOrd(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? toggleBackChaining(visualizer) : false;
}

export function moveBackChainingForOrd(ord: number, direction: BackChainingMarkerDirection): boolean {
  const visualizer = visualizerForOrd(ord);
  return visualizer ? moveBackChaining(visualizer, direction) : false;
}

export function handleBackChainingMarkerPointerDown(event: PointerEvent, ord: number): void {
  const visualizer = visualizerForOrd(ord);
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  const state = visualizer ? backChainingStateForVisualizer(visualizer) : null;
  if (!visualizer || !svg || !state) return;
  const readyState = ensureBackChainingBase(visualizer, state);
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
  const toggled = toggleBackChainingMarker(
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
  writeState(visualizer, emptyBackChainingState());
  syncSelectionToolbar(visualizer);
}

function ensureBackChainingBase(
  visualizer: VisualizerElement,
  state: BackChainingState,
): BackChainingState | null {
  const baseRegion = state.baseRegion ?? wholeFileBackChainingRegion(visualizer);
  if (!baseRegion) return null;
  const newBaseRegion = state.baseRegion === null;
  const markersMs = newBaseRegion ? defaultBackChainingMarkers(baseRegion) : state.markersMs;
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

function wholeFileBackChainingRegion(visualizer: VisualizerElement) {
  const durationMs = readVisualizerTargetDurationMs(visualizer);
  if (visualizer.dataset.hasTrack !== "true" || durationMs <= 0) return null;
  return {
    endMs: durationMs,
    mode: "selection" as const,
    startMs: 0,
  };
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
  writeState(visualizer, nextState);
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
  const baseState = ensureBackChainingBase(visualizer, state);
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
  writeState(visualizer, {
    ...state,
    practiceState: "paused",
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

function writeState(visualizer: VisualizerElement, state: BackChainingState): void {
  writeBackChainingState(visualizer, state);
  syncBackChainingToolbarButtons(visualizer);
}

function syncBackChainingToolbarButtons(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const controls = backChainingControlsForVisualizer(visualizer);
  const hasPlayableTrack = visualizer.dataset.hasTrack === "true" && readVisualizerTargetDurationMs(visualizer) > 0;
  const busy = document.body.dataset.aqeBusy === "true" || visualizer.dataset.graphBusy === "true";
  const practiceButton = buttonFor(ord, "aqe:back-chain-practice");
  if (practiceButton) {
    const playing = controls.practiceState === "playing";
    const canInitialize = controls.baseStartMs === null && hasPlayableTrack;
    practiceButton.disabled = busy || !(controls.canPractice || canInitialize);
    practiceButton.dataset.aqeButtonState = playing ? "pause" : "default";
    practiceButton.setAttribute("aria-pressed", playing ? "true" : "false");
    practiceButton.setAttribute("aria-disabled", practiceButton.disabled ? "true" : "false");
    const title = playing
      ? t("editor.command.back_chain_practice.pause_title")
      : t("editor.command.back_chain_practice.title");
    practiceButton.setAttribute("aria-label", title);
    setButtonTooltipContent(practiceButton, title);
  }
  const nextButton = buttonFor(ord, "aqe:back-chain-next");
  if (nextButton) {
    nextButton.disabled = busy || !controls.canNext;
    nextButton.dataset.aqeButtonState = controls.canNext ? "default" : "unavailable";
    nextButton.setAttribute("aria-disabled", nextButton.disabled ? "true" : "false");
    setButtonTooltipContent(nextButton, t("editor.command.back_chain_next.title"));
  }
}
