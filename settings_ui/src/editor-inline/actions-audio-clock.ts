import {
  allVisualizers,
  playRepeatMenuButtonForOrd,
  repeatButtonsForOrd,
} from "./dom-selectors.js";
import { formatRepeatPauseSeconds } from "../lib/audio-operation-parameters.js";
import { t } from "../lib/i18n.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import {
  audioClockReady as isAudioClockReady,
  clearAudioClockSource as clearAudioClockElementSource,
  configureAudioClock as configureAudioClockElement,
  installAudioClockHandlers as installAudioClockElementHandlers,
  pauseAudioClock as pauseAudioClockElement,
  resetAudioClockState as resetAudioClockElementState,
} from "./audio-clock.js";
import { logger } from "./logger.js";
import { completePlayback, handlePlaybackBoundary, playbackStateFor, startManualProgressClock, stopProgressClock } from "./playback-actions.js";
import { renderCursor } from "./visualizer-renderer.js";
import type { VisualizerElement } from "./types.js";
import { readFieldState, updateFieldState, writeFieldState } from "./field-state-store.js";
import {
  isRepeatPauseWaitingRuntime,
  readRepeatPauseSecondsRuntime,
  readTargetDurationMsForVisualizer,
  setTargetDurationMsForVisualizer,
} from "./visualizer-runtime-state.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

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
    onLoadedMetadata(durationMs) {
      if (readFieldState(fieldOrd(visualizer)).graph.hasTrack) return;
      const ord = fieldOrd(visualizer);
      updateFieldState(ord, (s) => ({
        ...s,
        graph: { ...s.graph, durationMs },
        playback: { ...s.playback, endMs: durationMs },
      }));
      if (readTargetDurationMsForVisualizer(visualizer, 0) <= 0) {
        setTargetDurationMsForVisualizer(visualizer, durationMs);
      }
      renderCursor(visualizer, readFieldState(ord).cursor.ms, durationMs);
    },
    onErrorDuringPlayback(cursorMs) {
      const ord = fieldOrd(visualizer);
      logger.warn("audio clock failed during playback", { ord });
      startManualProgressClock(visualizer, cursorMs);
    },
    onEndedDuringPlayback(durationMs) {
      handlePlaybackBoundary(visualizer, durationMs, { forceAudioPlay: true });
    },
  });
}

export function audioClockReady(visualizer: VisualizerElement | null): boolean {
  return isAudioClockReady(visualizer);
}

export function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = readFieldState(fieldOrd(visualizer)).graph.durationMs;
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}

export function setRepeatEnabled(visualizer: VisualizerElement, enabled: boolean): void {
  const ord = fieldOrd(visualizer);
  writeFieldState(ord, {
    ...readFieldState(ord),
    playback: { ...readFieldState(ord).playback, repeat: enabled },
  });
  for (const button of repeatButtonsForOrd(ord)) {
    button.ariaPressed = enabled ? "true" : "false";
    button.dataset.aqeButtonState = enabled ? "active" : "default";
  }
  const menuButton = playRepeatMenuButtonForOrd(ord);
  if (menuButton) {
    const pause = formatRepeatPauseSeconds(readRepeatPauseSecondsRuntime(visualizer));
    const title = t("editor.play.menu_title", {
      value: t("editor.play.current_value", {
        pause,
        repeat: enabled ? t("editor.play.repeat_on") : t("editor.play.repeat_off"),
      }),
    });
    setButtonTooltipContent(menuButton, title);
  }
  if (!enabled && isRepeatPauseWaitingRuntime(visualizer)) {
    completePlayback(visualizer);
  }
}

export function repeatEnabledFor(visualizer: VisualizerElement): boolean {
  return readFieldState(fieldOrd(visualizer)).playback.repeat;
}
