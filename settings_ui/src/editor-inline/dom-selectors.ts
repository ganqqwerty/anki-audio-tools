import { audioSourceForNode } from "./sound-source.js";
import type { EditorCommand, VisualizerElement } from "./types.js";

export function controlsForOrd(ord: number): HTMLElement | null {
  return document.querySelector<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${ord}"]`);
}

export function controlsForRawOrd(rawOrd: string): HTMLElement | null {
  return document.querySelector<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${rawOrd}"]`);
}

export function visualizerForOrd(ord: number): VisualizerElement | null {
  return document.querySelector<VisualizerElement>(`.aqe-visualizer[data-aqe-field-ord="${ord}"]`);
}

export function visualizerPlotForOrd(ord: number): HTMLElement | null {
  return visualizerForOrd(ord)?.querySelector<HTMLElement>(".aqe-visualizer-plot") ?? null;
}

export function currentAudioSourceForOrd(ord: number): string {
  const container = document.querySelector<HTMLElement>(`.field-container[data-index="${ord}"]`);
  const node = container?.querySelector<HTMLElement>('[contenteditable="true"]') ?? container;
  return audioSourceForNode(node) || audioSourceForNode(container);
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
  return controls?.querySelector<HTMLButtonElement>(".aqe-play-split-button .aqe-split-menu-button") ?? null;
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

export function allReviewerPanelTriggers(): HTMLButtonElement[] {
  return Array.from(document.querySelectorAll<HTMLButtonElement>(".aqe-review-audio-panel-trigger"));
}

export function reviewerPanelTargetForTrigger(trigger: HTMLButtonElement): HTMLElement | null {
  const ord = trigger.dataset.fieldOrd;
  const sourceFilename = trigger.dataset.aqeSourceFilename;
  if (!ord || !sourceFilename) return null;
  return Array.from(
    document.querySelectorAll<HTMLElement>(`.aqe-review-audio-target[data-field-ord="${ord}"]`),
  ).find((target) => target.dataset.aqeSourceFilename === sourceFilename) ?? null;
}
