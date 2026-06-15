import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import { t } from "../lib/i18n.js";
import { chorusingStateForVisualizer } from "./chorusing-dom.js";
import {
  resolveSelectionMarkerShift,
  type SelectionShiftDirection,
  type SelectionShiftDisabledReason,
  type SelectionShiftEdge,
} from "./selection-marker-shift.js";
import { selectionForVisualizer } from "./selection-controller.js";
import type { VisualizerElement } from "./types.js";
import { readFieldState } from "./field-state-store.js";
import { isEditorBusy } from "./editor-control-state.js";
import { readVisualizerTargetDurationMs } from "./visualizer-state.js";

const BUTTON_SPECS = [
  { edge: "start", direction: "previous" },
  { edge: "start", direction: "next" },
  { edge: "end", direction: "previous" },
  { edge: "end", direction: "next" },
] as const satisfies ReadonlyArray<{ direction: SelectionShiftDirection; edge: SelectionShiftEdge }>;

const VISUALIZER_ATTRIBUTE_FILTER = [
  "data-aqe-field-ord",
  "data-graph-busy",
  "data-has-track",
  "data-selection-active",
  "data-selection-draft-active",
  "data-selection-end-ms",
  "data-selection-start-ms",
  "data-chorusing-markers-ms",
];

const WRAPPER_ATTRIBUTE_FILTER = [
  "data-selection-end-edge-visible",
  "data-selection-overlay-ready",
  "data-selection-shift-hide-inner",
  "data-selection-start-edge-visible",
] as const;

export function selectionShiftMutationObserverOptions() {
  return {
    attributes: true,
    attributeFilter: [...VISUALIZER_ATTRIBUTE_FILTER, ...WRAPPER_ATTRIBUTE_FILTER],
    subtree: false,
  };
}

export function syncSelectionMarkerShiftButtons(visualizer: VisualizerElement): void {
  const wrapper = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
  const selection = selectionForVisualizer(visualizer);
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const s = readFieldState(ord);
  const busy = isEditorBusy() || s.graph.busy;
  const buttonsEnabled = visualizer.dataset.selectionMarkerShiftButtonsEnabled === "true";
  const hasTrack = s.graph.hasTrack;
  const draftActive = s.selection.draftActive;
  const overlayReady = wrapper?.dataset.selectionOverlayReady === "true";
  const hideInner = wrapper?.dataset.selectionShiftHideInner === "true";
  const startVisible = wrapper?.dataset.selectionStartEdgeVisible === "true";
  const endVisible = wrapper?.dataset.selectionEndEdgeVisible === "true";
  const shouldHideAll = !buttonsEnabled || !hasTrack || draftActive || !overlayReady || !selection;

  for (const spec of BUTTON_SPECS) {
    const button = buttonFor(visualizer, spec.edge, spec.direction);
    if (!button) continue;
    const hidden = shouldHideAll
      || (spec.edge === "start" ? !startVisible : !endVisible)
      || (hideInner && isInnerButton(spec.edge, spec.direction));
    if (hidden || !selection) {
      hideButton(button);
      continue;
    }

    button.hidden = false;
    button.setAttribute("aria-hidden", "false");
    const resolution = resolveSelectionMarkerShift(
      selection,
      spec.edge,
      spec.direction,
      chorusingStateForVisualizer(visualizer).markersMs,
      readVisualizerTargetDurationMs(visualizer),
    );
    const reason = resolution.disabledReason ? disabledReasonMessage(resolution.disabledReason) : undefined;
    const tooltip = tooltipWithDisabledClarification(buttonTitle(spec.edge, spec.direction), busy && !reason ? t("tooltip.disabled.editor_busy") : reason);
    button.disabled = busy || resolution.nextRange === null;
    button.dataset.aqeButtonState = button.disabled ? "unavailable" : "default";
    button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
    setButtonTooltipContent(button, tooltip);
  }
}

function buttonFor(
  visualizer: VisualizerElement,
  edge: SelectionShiftEdge,
  direction: SelectionShiftDirection,
): HTMLButtonElement | null {
  return visualizer.querySelector<HTMLButtonElement>(
    `.aqe-selection-shift-button[data-selection-edge="${edge}"][data-selection-direction="${direction}"]`,
  );
}

function hideButton(button: HTMLButtonElement): void {
  button.hidden = true;
  button.disabled = true;
  button.dataset.aqeButtonState = "unavailable";
  button.setAttribute("aria-disabled", "true");
  button.setAttribute("aria-hidden", "true");
}

function isInnerButton(edge: SelectionShiftEdge, direction: SelectionShiftDirection): boolean {
  return (edge === "start" && direction === "next") || (edge === "end" && direction === "previous");
}

function buttonTitle(edge: SelectionShiftEdge, direction: SelectionShiftDirection): string {
  if (edge === "start" && direction === "previous") return t("editor.selection_shift.start_previous");
  if (edge === "start" && direction === "next") return t("editor.selection_shift.start_next");
  if (edge === "end" && direction === "previous") return t("editor.selection_shift.end_previous");
  return t("editor.selection_shift.end_next");
}

function disabledReasonMessage(reason: SelectionShiftDisabledReason): string {
  if (reason === "no_previous") return t("editor.selection_shift.disabled.no_previous");
  if (reason === "no_next") return t("editor.selection_shift.disabled.no_next");
  if (reason === "crosses_other_edge") return t("editor.selection_shift.disabled.crosses_other_edge");
  return t("editor.selection_shift.disabled.too_short");
}
