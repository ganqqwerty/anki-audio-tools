import { focusAndSendCommand, setCursorIntent } from "./bridge.js";
import { logger } from "./logger.js";
import { effectivePlaybackRegion } from "./selection-controller.js";
import { readFieldState, writeFieldState } from "./field-state-store.js";
import { renderCursor } from "./visualizer-renderer.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";
import type { CursorIntent, PlaybackState, VisualizerElement } from "./types.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
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
  if (!notifyPython) return;
  window.__aqeActiveField = Number(visualizer.dataset.aqeFieldOrd || "0");
  const region = effectivePlaybackRegion(visualizer);
  const intent: CursorIntent = {
    cursorMs: Math.round(clamped),
    endMs: Math.round(region.endMs),
    previousPlaybackState: options.previousPlaybackState || readFieldState(ord).playback.state,
    regionMode: region.mode,
    restartPlayback: !!options.restartPlayback,
  };
  if (options.engine) intent.engine = options.engine;
  setCursorIntent(intent);
  logger.info("cursor committed", intent);
  focusAndSendCommand(window.__aqeActiveField, "aqe:set-cursor");
}
