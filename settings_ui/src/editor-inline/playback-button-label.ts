import { setCommandButtonLabel } from "./control-actions.js";
import { syncSelectionToolbar } from "./selection-toolbar-state.js";
import type { VisualizerElement } from "./types.js";

export function setPlaybackButtonLabelForVisualizer(visualizer: VisualizerElement, label: string): void {
  setCommandButtonLabel(Number(visualizer.dataset.aqeFieldOrd || "0"), "aqe:play", label);
  syncSelectionToolbar(visualizer);
}
