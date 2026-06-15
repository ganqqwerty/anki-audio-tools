import {
  audioClockReady,
  clearAudioClockSource,
  pauseAudioClock,
  seekAudioClock,
} from "./audio-clock.js";
import { playbackCompletionCursor } from "./playback-model.js";
import { clearPlaybackFrame } from "./playback-controller-frame.js";
import type { PlaybackControllerDependencies } from "./playback-controller.js";
import type { VisualizerElement } from "./types.js";
import { writeFieldState, readFieldState } from "./field-state-store.js";
import type { EditorFieldState } from "./field-state.js";
import { ensurePlaybackCursorVisible } from "./viewport-actions.js";
import { currentProgressMs } from "./playback-controller-audio.js";
import { activePlaybackPass } from "./playback-controller-pass.js";
import {
  preserveStatusOnPlaybackEndRuntime,
  setPreserveStatusOnPlaybackEndRuntime,
} from "./visualizer-runtime-state.js";

function fieldState(visualizer: VisualizerElement): EditorFieldState {
  return readFieldState(Number(visualizer.dataset.aqeFieldOrd || "0"));
}

export function completePlayback(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): void {
  const s = fieldState(visualizer);
  const resetCursorMs = playbackCompletionCursor(activePlaybackPass(visualizer, deps));
  const preserveStatus = preserveStatusOnPlaybackEndRuntime(visualizer);
  stopProgressClock(visualizer, deps);
  deps.setCursor(visualizer, resetCursorMs, false, { updateAnchor: false });
  ensurePlaybackCursorVisible(visualizer, resetCursorMs);
  if (audioClockReady(visualizer)) {
    seekAudioClock(visualizer, resetCursorMs, s.graph.durationMs);
  }
  if (preserveStatus) {
    deps.restoreStatus(s.ord);
  } else {
    deps.clearStatus(s.ord);
  }
  setPreserveStatusOnPlaybackEndRuntime(visualizer, false);
  window.__aqeActiveField = s.ord;
  deps.focusAndSendCommand(s.ord, "aqe:play-ended");
}

export function pauseProgressClock(visualizer: VisualizerElement, deps: PlaybackControllerDependencies): void {
  const currentMs = currentProgressMs(visualizer);
  if (currentMs !== null) {
    deps.setCursor(visualizer, currentMs, false, { updateAnchor: false });
  }
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  const s = fieldState(visualizer);
  writeFieldState(s.ord, {
    ...s,
    playback: { ...s.playback, state: "paused", clockMode: "stopped" },
  });
  deps.setPlaybackButtonLabel(visualizer, "Play");
}

export function stopProgressClock(
  visualizer: VisualizerElement,
  deps: PlaybackControllerDependencies,
  options: { clearAudio?: boolean; clearEngine?: boolean } = {},
): void {
  clearPlaybackFrame(visualizer);
  pauseAudioClock(visualizer);
  const s = fieldState(visualizer);
  writeFieldState(s.ord, {
    ...s,
    playback: {
      ...s.playback,
      state: "stopped",
      clockMode: "stopped",
      resumeRequiresRestart: false,
      engine: options.clearEngine !== false ? "" : s.playback.engine,
    },
  });
  if (options.clearAudio) {
    clearAudioClockSource(visualizer);
  }
  deps.setPlaybackButtonLabel(visualizer, "Play");
}
