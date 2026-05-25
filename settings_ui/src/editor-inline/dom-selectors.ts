import { audioSourceForNode } from "./sound-source.js";
import type { EditorCommand, VisualizerElement } from "./types.js";

export function controlsForOrd(ord: number): HTMLElement | null {
  return document.querySelector<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${ord}"]`);
}

export function visualizerForOrd(ord: number): VisualizerElement | null {
  return document.querySelector<VisualizerElement>(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
}

export function visualizerPlotForOrd(ord: number): HTMLElement | null {
  return visualizerForOrd(ord)?.querySelector<HTMLElement>(".aqe-visualizer-plot") ?? null;
}

export function selectionToolbarForOrd(ord: number): HTMLElement | null {
  return visualizerForOrd(ord)?.querySelector<HTMLElement>(".aqe-selection-toolbar") ?? null;
}

export function selectionToolbarDotForOrd(ord: number): SVGSVGElement | null {
  return visualizerForOrd(ord)?.querySelector<SVGSVGElement>(".aqe-selection-toolbar-dot") ?? null;
}

export function currentAudioSourceForOrd(ord: number): string {
  const container = document.querySelector<HTMLElement>(`.field-container[data-index="${ord}"]`);
  const node = container?.querySelector<HTMLElement>('[contenteditable="true"]') ?? container;
  return audioSourceForNode(node) || audioSourceForNode(container);
}

export function fieldPreferenceNodeForOrd(ord: number): HTMLElement | null {
  const container = document.querySelector<HTMLElement>(`.field-container[data-index="${ord}"]`);
  if (container) {
    return container.querySelector<HTMLElement>('[contenteditable="true"]') || container;
  }
  return document.querySelector<HTMLElement>(
    `[data-field-ord="${ord}"], [data-ord="${ord}"], [data-index="${ord}"]`,
  );
}

export function allFieldPreferenceNodes(): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>("[data-aqe-selection-toolbar-preferred-collapsed]"));
}

export function buttonFor(ord: number, command: EditorCommand): HTMLButtonElement | null {
  const controls = controlsForOrd(ord);
  return controls?.querySelector<HTMLButtonElement>(`[data-aqe-command="${command}"]`) ?? null;
}

export function graphButton(ord: number): HTMLButtonElement | null {
  return buttonFor(ord, "aqe:analyze");
}

export function playButton(ord: number): HTMLButtonElement | null {
  return buttonFor(ord, "aqe:play");
}

export function repeatButtonForOrd(ord: number): HTMLButtonElement | null {
  const controls = controlsForOrd(ord);
  return controls?.querySelector<HTMLButtonElement>(".aqe-repeat-button") ?? null;
}

export function playRepeatMenuButtonForOrd(ord: number): HTMLButtonElement | null {
  const controls = controlsForOrd(ord);
  return controls?.querySelector<HTMLButtonElement>(".aqe-play-repeat-menu-button") ?? null;
}

export function allButtons(): HTMLButtonElement[] {
  return Array.from(document.querySelectorAll<HTMLButtonElement>(".aqe-button"));
}

export function allControls(): HTMLElement[] {
  return Array.from(document.querySelectorAll<HTMLElement>(".aqe-controls"));
}

export function allRepeatButtons(): HTMLButtonElement[] {
  return Array.from(document.querySelectorAll<HTMLButtonElement>(".aqe-repeat-button"));
}

export function allVisualizers(): VisualizerElement[] {
  return Array.from(document.querySelectorAll<VisualizerElement>(".aqe-visualizer"));
}
