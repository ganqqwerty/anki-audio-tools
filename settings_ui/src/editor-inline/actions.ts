import {
  allVisualizers,
  repeatButtonForOrd,
  visualizerForOrd,
} from "./dom-selectors.js";
import {
  focusAndSendCommand,
  setCursorIntent,
} from "./bridge.js";
import {
  audioClockReady as isAudioClockReady,
  clearAudioClockSource as clearAudioClockElementSource,
  configureAudioClock as configureAudioClockElement,
  installAudioClockHandlers as installAudioClockElementHandlers,
  pauseAudioClock as pauseAudioClockElement,
  resetAudioClockState as resetAudioClockElementState,
  seekAudioClock as seekAudioClockElement,
} from "./audio-clock.js";
import { logger } from "./logger.js";
import type { PlaybackRegion } from "./playback-state.js";
import type {
  CursorIntent,
  PlaybackRequest,
  PlaybackState,
  VisualizerElement,
} from "./types.js";
import {
  syncRegionDeleteControl,
} from "./region-delete-state.js";
import {
  shouldTreatSelectionGestureAsClick as isClickLikeSelectionGesture,
  type SelectionResizeEdge,
} from "./selection-state.js";
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
  startSelectionGesture as startSelectionGestureFlow,
  type SelectionGestureDependencies,
} from "./selection-gestures.js";
import {
  renderCursor,
} from "./visualizer-renderer.js";
import {
  clearPlaybackFrame as clearPlaybackFrameFromController,
  type PlaybackControllerDependencies,
} from "./playback-controller.js";
export { popEditorFrontendLog, popPendingGraphAnalysisRequest } from "./bridge.js";
import {
  clearStatus,
  repeatDefaultFromConfig,
} from "./control-actions.js";
export {
  anyBusy,
  clearStatus,
  repeatDefaultFromConfig,
  setCommandButtonLabel,
  setControlsBusy,
  setStatus,
} from "./control-actions.js";
export { send } from "./command-actions.js";
import {
  prepareForNewNote,
  requestDefaultGraph,
  requestGraph,
  requestPendingGraphRedraw,
  resetGraphAfterEdit,
  setVisualizer,
  setVisualizerStatus,
  setVisualizerStatusFromPython,
} from "./graph-actions.js";
import {
  audioProgressMs,
  completePlayback,
  currentProgressMs,
  getCursorIntent,
  getCursorMs,
  getPlaybackRequest,
  handleHtmlPlaybackCommand,
  handlePlaybackBoundary,
  manualProgressMs,
  paintProgressFromClock,
  pauseProgressClock,
  playbackEngineFor,
  playbackRequest,
  playbackStateFor,
  sendPlaybackRequest,
  setPlaybackButtonLabel,
  setPlaybackState,
  startAudioProgressClock,
  startEditorHtmlPlayback,
  startManualProgressClock,
  startProgressClock,
  stopEditorPlayback,
  stopProgressClock,
} from "./playback-actions.js";
export {
  audioProgressMs,
  completePlayback,
  currentProgressMs,
  getCursorIntent,
  getCursorMs,
  getPlaybackRequest,
  handleHtmlPlaybackCommand,
  manualProgressMs,
  paintProgressFromClock,
  pauseProgressClock,
  playbackEngineFor,
  playbackRequest,
  sendPlaybackRequest,
  setPlaybackButtonLabel,
  setPlaybackState,
  startAudioProgressClock,
  startEditorHtmlPlayback,
  startManualProgressClock,
  startProgressClock,
  stopEditorPlayback,
  stopProgressClock,
};
export { prepareForNewNote, requestDefaultGraph, requestGraph, requestPendingGraphRedraw, resetGraphAfterEdit, setVisualizer, setVisualizerStatus, setVisualizerStatusFromPython };

export function stopOtherPlayback(activeVisualizer: VisualizerElement): void {
  for (const visualizer of allVisualizers()) {
    if (visualizer !== activeVisualizer && playbackStateFor(visualizer) !== "stopped") {
      stopProgressClock(visualizer);
    }
  }
}

export function resetAudioClockState(visualizer: VisualizerElement): void {
  resetAudioClockElementState(visualizer);
}

export function clearPlaybackFrame(visualizer: VisualizerElement): void {
  clearPlaybackFrameFromController(visualizer);
}

export function pauseAudioClock(visualizer: VisualizerElement): void {
  pauseAudioClockElement(visualizer);
}

export function clearAudioClockSource(visualizer: VisualizerElement): void {
  clearAudioClockElementSource(visualizer);
}

export function configureAudioClock(visualizer: VisualizerElement, filename: string): void {
  configureAudioClockElement(visualizer, filename);
}

export function installAudioClockHandlers(visualizer: VisualizerElement): void {
  installAudioClockElementHandlers(visualizer, {
    onErrorDuringPlayback() {
      logger.warn("audio clock failed during playback", { ord: visualizer.dataset.aqeFieldOrd });
      startManualProgressClock(visualizer, Number(visualizer.dataset.cursorMs || "0"));
    },
    onEndedDuringPlayback() {
      handlePlaybackBoundary(visualizer, Number(visualizer.dataset.durationMs || "0"), { forceAudioPlay: true });
    },
  });
}

export function audioClockReady(visualizer: VisualizerElement | null): boolean {
  return isAudioClockReady(visualizer);
}

export function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}

export function selectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  return selectionForVisualizerFromController(visualizer);
}

export function draftSelectionForVisualizer(visualizer: VisualizerElement | null): PlaybackRegion | null {
  return draftSelectionForVisualizerFromController(visualizer);
}

export function effectivePlaybackRegion(visualizer: VisualizerElement): PlaybackRegion {
  return effectivePlaybackRegionFromController(visualizer);
}

export function setRepeatEnabled(visualizer: VisualizerElement, enabled: boolean): void {
  visualizer.dataset.repeatEnabled = enabled ? "true" : "false";
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const button = repeatButtonForOrd(ord);
  if (button) {
    button.ariaPressed = enabled ? "true" : "false";
    button.dataset.aqeButtonState = enabled ? "active" : "default";
  }
}

export function setRepeatEnabledForOrd(ord: number, enabled: boolean): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  setRepeatEnabled(visualizer, enabled);
  return true;
}

export function clearSelectionDraft(
  visualizer: VisualizerElement,
  options: { redraw?: boolean } = {},
): void {
  clearSelectionDraftFromController(visualizer, options);
}

export function setSelectionDraft(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  options: { redraw?: boolean } = {},
): boolean {
  return setSelectionDraftFromController(visualizer, startMs, endMs, options);
}

export function commitSelectionDraft(
  visualizer: VisualizerElement,
  options: { updateCursor?: boolean } = {},
): boolean {
  const committed = commitSelectionDraftFromController(visualizer, selectionControllerDependencies(), options);
  syncRegionDeleteControl(visualizer);
  return committed;
}

export function clearSelection(
  visualizer: VisualizerElement,
  options: { resetPlaybackRegion?: boolean } = {},
): void {
  clearSelectionFromController(visualizer, options);
  syncRegionDeleteControl(visualizer);
}

export function setSelection(
  visualizer: VisualizerElement,
  startMs: number,
  endMs: number,
  options: { updateCursor?: boolean } = {},
): boolean {
  const selected = setSelectionFromController(visualizer, startMs, endMs, selectionControllerDependencies(), options);
  syncRegionDeleteControl(visualizer);
  return selected;
}

export function initializePlaybackRegionState(visualizer: VisualizerElement): void {
  visualizer.dataset.playbackStartMs = "0";
  visualizer.dataset.playbackEndMs = String(Number(visualizer.dataset.durationMs || "0") || 0);
  visualizer.dataset.playbackRegionMode = "full";
  setRepeatEnabled(visualizer, repeatDefaultFromConfig());
  clearSelection(visualizer, { resetPlaybackRegion: false });
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

export function repeatEnabledFor(visualizer: VisualizerElement): boolean {
  return visualizer.dataset.repeatEnabled === "true";
}

export function playbackControllerDependencies(): PlaybackControllerDependencies {
  return {
    clearStatus,
    effectivePlaybackRegion,
    focusAndSendCommand,
    playbackEngineFor,
    repeatEnabledFor,
    setCursor,
    setPlaybackButtonLabel,
    stopOtherPlayback,
  };
}

export function playbackRequestForStart(
  visualizer: VisualizerElement,
  ord: number,
  startMs: number,
  engine: "html" | "native" | "" = playbackEngineFor(visualizer),
): PlaybackRequest {
  const region = effectivePlaybackRegion(visualizer);
  return {
    ord,
    action: "start",
    cursorMs: Math.round(clampProgressMs(visualizer, startMs)),
    endMs: Math.round(region.endMs),
    engine,
    loop: repeatEnabledFor(visualizer),
    regionMode: region.mode,
  };
}

export function seekAudioClock(visualizer: VisualizerElement, ms: number): boolean {
  return seekAudioClockElement(visualizer, ms, Number(visualizer.dataset.durationMs || "0"));
}

export function setCursor(
  visualizer: VisualizerElement,
  ms: number,
  notifyPython: boolean,
  options: {
    engine?: "html" | "native" | "";
    previousPlaybackState?: PlaybackState;
    restartPlayback?: boolean;
    updateAnchor?: boolean;
  } = {},
): void {
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const clamped = Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
  visualizer.dataset.cursorMs = String(Math.round(clamped));
  visualizer.dataset.progressMs = String(Math.round(clamped));
  if (options.updateAnchor !== false) {
    visualizer.dataset.anchorMs = String(Math.round(clamped));
  }
  renderCursor(visualizer, clamped, durationMs);
  if (notifyPython) {
    window.__aqeActiveField = Number(visualizer.dataset.aqeFieldOrd || "0");
    const intent: CursorIntent = {
      cursorMs: Math.round(clamped),
      previousPlaybackState: options.previousPlaybackState || playbackStateFor(visualizer),
      restartPlayback: !!options.restartPlayback,
    };
    if (options.engine) intent.engine = options.engine;
    setCursorIntent(intent);
    logger.info("cursor committed", intent);
    focusAndSendCommand(window.__aqeActiveField, "aqe:set-cursor");
  }
}

export function startCursorDrag(event: PointerEvent, visualizer: VisualizerElement, ord: number, notifyPython: boolean): void {
  startCursorDragGesture(event, visualizer, ord, notifyPython, selectionGestureDependencies());
}

export function startSelectionGesture(event: PointerEvent, visualizer: VisualizerElement, ord: number): void {
  startSelectionGestureFlow(event, visualizer, ord, selectionGestureDependencies());
}

export function startSelectionResizeGesture(
  event: PointerEvent,
  _ord: number,
  _edge: SelectionResizeEdge,
): void {
  event.preventDefault();
  event.stopPropagation();
}

export function handleVisualizerPointerDown(event: PointerEvent, ord: number): void {
  visualizerForOrd(ord)?.focus();
  handleVisualizerPointerDownGesture(event, ord, selectionGestureDependencies());
}
