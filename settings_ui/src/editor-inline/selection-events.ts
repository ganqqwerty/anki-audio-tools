import type { VisualizerElement } from "./types.js";

export type SelectionMutationOrigin = "back-chaining" | "system" | "user";

export interface SelectionChangedDetail {
  origin: SelectionMutationOrigin;
}

export const SELECTION_CHANGED_EVENT = "aqe-selection-changed";

export function notifySelectionChanged(
  visualizer: VisualizerElement,
  origin: SelectionMutationOrigin = "user",
): void {
  visualizer.dispatchEvent(new CustomEvent<SelectionChangedDetail>(SELECTION_CHANGED_EVENT, {
    bubbles: false,
    detail: { origin },
  }));
}
