import { htmlAudioReadinessForOrd } from "./audio-readiness.js";
import {
  dispatchHtmlAudioSessionEvent,
} from "./html-audio-session-controller.js";
import { disableEditorPracticeRepeat } from "./editor-practice-controller.js";
import type { VisualizerElement } from "./types.js";
import { readFieldState, updateFieldState } from "./field-state-store.js";
import {
  projectRepeatEnabled,
  repeatEnabledFor,
} from "./repeat-control-projection.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

export function resetAudioClockState(visualizer: VisualizerElement): void {
  const ord = fieldOrd(visualizer);
  updateFieldState(ord, (state) => ({
    ...state,
    playback: { ...state.playback, clockMode: "stopped" },
  }));
}

export function pauseAudioClock(visualizer: VisualizerElement): void {
  const ord = fieldOrd(visualizer);
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs: readFieldState(ord).cursor.ms,
    type: "StopRequested",
  });
}

export function clearAudioClockSource(visualizer: VisualizerElement): void {
  dispatchHtmlAudioSessionEvent(fieldOrd(visualizer), { type: "SourceCleared" });
}

export function configureAudioClock(visualizer: VisualizerElement, filename: string, cursorMs?: number): void {
  const ord = fieldOrd(visualizer);
  if (!filename) {
    clearAudioClockSource(visualizer);
    return;
  }
  dispatchHtmlAudioSessionEvent(ord, {
    cursorMs: cursorMs ?? readFieldState(ord).cursor.ms,
    source: { kind: "source", sourceFilename: filename },
    type: "SourceConfigured",
  });
}

export function installAudioClockHandlers(_visualizer: VisualizerElement): void {
  // Stable media handlers are owned by HtmlAudioPort construction.
}

export function audioClockReady(visualizer: VisualizerElement | null): boolean {
  return visualizer !== null
    && htmlAudioReadinessForOrd(fieldOrd(visualizer)).ready;
}

export function clampProgressMs(visualizer: VisualizerElement, ms: number): number {
  const durationMs = readFieldState(fieldOrd(visualizer)).graph.durationMs;
  return Math.max(0, Math.min(Number(ms) || 0, durationMs || 0));
}

export function setRepeatEnabled(visualizer: VisualizerElement, enabled: boolean): void {
  projectRepeatEnabled(visualizer, enabled);
  if (!enabled) disableEditorPracticeRepeat(fieldOrd(visualizer));
}
export { repeatEnabledFor };
