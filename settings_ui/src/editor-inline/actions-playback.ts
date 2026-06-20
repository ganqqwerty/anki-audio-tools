import { visualizerForOrd } from "./dom-selectors.js";
import { focusAndSendCommand, setCursorIntent } from "./bridge.js";
import { seekAudioClock as seekAudioClockElement } from "./audio-clock.js";
import { logger } from "./logger.js";
import type {
  CursorIntent,
  PlaybackRequest,
  PlaybackState,
  VisualizerElement,
} from "./types.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import {
  clearPlaybackStatusForOrd,
  repeatDefaultFromConfig,
  restoreStatusForOrd,
} from "./control-actions.js";
import { playbackEngineFor, playbackStateFor, setPlaybackButtonLabel } from "./playback-actions.js";
import { clearPlaybackFrame as clearPlaybackFrameFromController } from "./playback-controller-frame.js";
import type { PlaybackControllerDependencies } from "./playback-controller.js";
import {
  clampProgressMs,
  repeatEnabledFor,
  setRepeatEnabled,
  stopOtherPlayback,
} from "./actions-audio-clock.js";
import { renderCursor } from "./visualizer-renderer.js";
import {
  clearSelection as clearSelectionFromController,
  effectivePlaybackRegion as effectivePlaybackRegionFromController,
} from "./selection-controller.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import { notifySelectionChanged } from "./selection-events.js";
import { readFieldState, writeFieldState } from "./field-state-store.js";
import { handleChorusingLoopBoundary } from "./chorusing-controller.js";
import {
  setPlaybackPassRuntime,
  setRepeatPauseSecondsRuntime,
} from "./visualizer-runtime-state.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

export function clearPlaybackFrame(visualizer: VisualizerElement): void {
  clearPlaybackFrameFromController(visualizer);
}

export function setRepeatEnabledForOrd(ord: number, enabled: boolean): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  setRepeatEnabled(visualizer, enabled);
  return true;
}

export function setRepeatPauseSeconds(visualizer: VisualizerElement, seconds: number): void {
  setRepeatPauseSecondsRuntime(visualizer, seconds);
}

export function setRepeatPauseSecondsForOrd(ord: number, seconds: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  setRepeatPauseSeconds(visualizer, seconds);
  return true;
}

export function playbackControllerDependencies(): PlaybackControllerDependencies {
  return {
    clearStatus: clearPlaybackStatusForOrd,
    effectivePlaybackRegion: effectivePlaybackRegionFromController,
    focusAndSendCommand,
    handleLoopBoundary: handleChorusingLoopBoundary,
    playbackEngineFor,
    repeatEnabledFor,
    restoreStatus: restoreStatusForOrd,
    setCursor,
    setPlaybackButtonLabel,
    stopOtherPlayback,
  };
}

export function playbackRequestForStart(
  visualizer: VisualizerElement,
  ord: number,
  startMs: number,
): PlaybackRequest {
  const region = effectivePlaybackRegionFromController(visualizer);
  return {
    ord,
    action: "start",
    cursorMs: Math.round(clampProgressMs(visualizer, startMs)),
    endMs: Math.round(region.endMs),
    engine: playbackEngineFor(visualizer),
    loop: repeatEnabledFor(visualizer),
    regionMode: region.mode,
  };
}

export function seekAudioClock(visualizer: VisualizerElement, ms: number): boolean {
  return seekAudioClockElement(visualizer, ms, readVisualizerTargetDurationMs(visualizer));
}

export function setCursor(
  visualizer: VisualizerElement,
  ms: number,
  notifyPython: boolean,
  options: {
    engine?: "html" | "";
    previousPlaybackState?: PlaybackState;
    restartPlayback?: boolean;
    updateAnchor?: boolean;
  } = {},
): void {
  const ord = fieldOrd(visualizer);
  const s = readFieldState(ord);
  const targetDurationMs = readVisualizerTargetDurationMs(visualizer);
  const clamped = Math.max(0, Math.min(Number(ms) || 0, targetDurationMs || 0));
  writeFieldState(ord, {
    ...s,
    cursor: {
      anchorMs: options.updateAnchor !== false ? Math.round(clamped) : s.cursor.anchorMs,
      ms: Math.round(clamped),
      progressMs: Math.round(clamped),
    },
  });
  renderCursor(visualizer, clamped, s.graph.durationMs);
  if (notifyPython) {
    window.__aqeActiveField = Number(visualizer.dataset.aqeFieldOrd || "0");
    const region = effectivePlaybackRegionFromController(visualizer);
    const intent: CursorIntent = {
      cursorMs: Math.round(clamped),
      endMs: Math.round(region.endMs),
      previousPlaybackState: options.previousPlaybackState || playbackStateFor(visualizer),
      regionMode: region.mode,
      restartPlayback: !!options.restartPlayback,
    };
    if (options.engine) intent.engine = options.engine;
    setCursorIntent(intent);
    logger.info("cursor committed", intent);
    focusAndSendCommand(window.__aqeActiveField, "aqe:set-cursor");
  }
}

export function initializePlaybackRegionState(visualizer: VisualizerElement): void {
  const s = readFieldState(fieldOrd(visualizer));
  writeFieldState(s.ord, {
    ...s,
    playback: {
      ...s.playback,
      endMs: s.graph.durationMs || 0,
      regionMode: "full",
      startMs: 0,
    },
  });
  setPlaybackPassRuntime(visualizer, {
    endMs: s.graph.durationMs || 0,
    loop: repeatDefaultFromConfig(),
    regionMode: "full",
    resetCursorMs: 0,
    startMs: 0,
  });
  setRepeatEnabled(visualizer, repeatDefaultFromConfig());
  clearSelectionFromController(visualizer, { resetPlaybackRegion: false });
  notifySelectionChanged(visualizer, "system");
  syncSelectionToolbar(visualizer);
}
