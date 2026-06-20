import { startSourceHtmlPlayback } from "./source-playback-controller.js";
import type { PlaybackRequest, VisualizerElement } from "./types.js";
import { setPreserveStatusOnPlaybackEndRuntime } from "./visualizer-runtime-state.js";

export function startSourcePlaybackAction(visualizer: VisualizerElement, request: PlaybackRequest): boolean {
  setPreserveStatusOnPlaybackEndRuntime(visualizer, request.source === "post_edit");
  return startSourceHtmlPlayback(visualizer, { ...request, engine: "html" });
}
