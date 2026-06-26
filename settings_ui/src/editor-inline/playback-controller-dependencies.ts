import { focusAndSendCommand } from "./bridge.js";
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

export type PlaybackControllerDependencyOverrides = Partial<
  Pick<PlaybackControllerDependencies, "handleLoopBoundary">
>;

export function playbackControllerDependencies(
  overrides: PlaybackControllerDependencyOverrides = {},
): PlaybackControllerDependencies {
  const deps: PlaybackControllerDependencies = {
    clearStatus: clearPlaybackStatusForOrd,
    effectivePlaybackRegion,
    focusAndSendCommand,
    playbackEngineFor: () => "html",
    repeatEnabledFor,
    restoreStatus: restoreStatusForOrd,
    setCursor,
    setPlaybackButtonLabel: setPlaybackButtonLabelForVisualizer,
    stopOtherPlayback: (activeVisualizer) => stopOtherPlayback(activeVisualizer, overrides),
  };
  return { ...deps, ...overrides };
}

function stopOtherPlayback(
  activeVisualizer: VisualizerElement,
  overrides: PlaybackControllerDependencyOverrides,
): void {
  for (const visualizer of allVisualizers()) {
    if (visualizer === activeVisualizer || playbackStopped(visualizer)) continue;
    stopProgressClockFromController(visualizer, playbackControllerDependencies(overrides));
  }
}
