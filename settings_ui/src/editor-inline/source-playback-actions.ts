import { startSourceHtmlPlayback } from "./source-playback-controller.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";

export function startSourcePlaybackAction(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  return startSourceHtmlPlayback(visualizer, { ...request, engine: "html" });
}
