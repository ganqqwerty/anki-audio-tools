import { focusAndSendCommand } from "./bridge.js";
import { handleChorusingLoopBoundary } from "./chorusing-controller.js";
import {
  clearPlaybackStatusForOrd,
  restoreStatusForOrd,
} from "./control-actions.js";
import { allVisualizers } from "./dom-selectors.js";
import { setCursor } from "./cursor-actions.js";
import { setPlaybackButtonLabelForVisualizer } from "./playback-button-label.js";
import {
  playbackStopped,
  stopProgressClock as stopProgressClockFromController,
  type PlaybackControllerDependencies,
} from "./playback-controller.js";
import { repeatEnabledFor } from "./repeat-control-projection.js";
import { effectivePlaybackRegion } from "./selection-controller.js";
import type { VisualizerElement } from "./types.js";

export function playbackControllerDependencies(): PlaybackControllerDependencies {
  return {
    clearStatus: clearPlaybackStatusForOrd,
    effectivePlaybackRegion,
    focusAndSendCommand,
    handleLoopBoundary: handleChorusingLoopBoundary,
    playbackEngineFor: () => "html",
    repeatEnabledFor,
    restoreStatus: restoreStatusForOrd,
    setCursor,
    setPlaybackButtonLabel: setPlaybackButtonLabelForVisualizer,
    stopOtherPlayback,
  };
}

function stopOtherPlayback(activeVisualizer: VisualizerElement): void {
  for (const visualizer of allVisualizers()) {
    if (visualizer === activeVisualizer || playbackStopped(visualizer)) continue;
    stopProgressClockFromController(visualizer, playbackControllerDependencies());
  }
}
