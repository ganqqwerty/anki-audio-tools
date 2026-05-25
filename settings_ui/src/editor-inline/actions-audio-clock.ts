import {
  allVisualizers,
  playRepeatMenuButtonForOrd,
  repeatButtonForOrd,
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
      if (visualizer.dataset.hasTrack === "true") return;
      visualizer.dataset.durationMs = String(durationMs);
      if ((Number(visualizer.dataset.targetDurationMs || "0") || 0) <= 0) {
        visualizer.dataset.targetDurationMs = String(durationMs);
      }
      visualizer.dataset.playbackEndMs = String(durationMs);
      renderCursor(visualizer, Number(visualizer.dataset.cursorMs || "0"), durationMs);
    },
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

export function setRepeatEnabled(visualizer: VisualizerElement, enabled: boolean): void {
  visualizer.dataset.repeatEnabled = enabled ? "true" : "false";
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const button = repeatButtonForOrd(ord);
  if (button) {
    button.ariaPressed = enabled ? "true" : "false";
    button.dataset.aqeButtonState = enabled ? "active" : "default";
  }
  const menuButton = playRepeatMenuButtonForOrd(ord);
  if (menuButton) {
    const pause = formatRepeatPauseSeconds(Number(visualizer.dataset.repeatPauseSeconds || "0"));
    const title = t("editor.play.menu_title", {
      value: t("editor.play.current_value", {
        pause,
        repeat: enabled ? t("editor.play.repeat_on") : t("editor.play.repeat_off"),
      }),
    });
    menuButton.dataset.aqeButtonState = enabled ? "active" : "default";
    setButtonTooltipContent(menuButton, title);
  }
  if (!enabled && visualizer.dataset.repeatPauseWaiting === "true") {
    completePlayback(visualizer);
  }
}

export function repeatEnabledFor(visualizer: VisualizerElement): boolean {
  return visualizer.dataset.repeatEnabled === "true";
}
