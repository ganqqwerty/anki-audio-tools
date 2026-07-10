import { readFileSync } from "node:fs";

import { handlePlaybackBoundary, setRepeatEnabledForOrd } from "../src/editor-inline/actions.js";
import { initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  setChorusingAutoAdvanceForField,
  setChorusingRepeatCountForField,
} from "../src/editor-inline/split-button-state.js";
import {
  dispatchGraphPointer,
  graphClientX,
  prepareHtmlAudio,
  setFullGraphViewport,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

const visualizerCss = readFileSync("src/editor-inline/styles/visualizer.css", "utf8");
const selectionCss = readFileSync("src/editor-inline/styles/selection.css", "utf8");

type EditorRuntimeOverrides = Partial<Parameters<typeof initializeEditorRuntime>[0]>;

export function installChorusingVisualizerStyles(): void {
  if (document.querySelector("style[data-aqe-test-visualizer-styles]")) return;
  const style = document.createElement("style");
  style.dataset.aqeTestVisualizerStyles = "true";
  style.textContent = `${visualizerCss}\n${selectionCss}`;
  document.head.appendChild(style);
}

export async function prepareChorusingGraph(
  overrides: EditorRuntimeOverrides = {},
): Promise<{ row: SVGGElement; svg: SVGSVGElement }> {
  const config = { audioFieldIndices: [0], repeatPlaybackByDefault: false, ...overrides };
  initializeEditorRuntime(config);
  scan(config);
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);
  await Promise.resolve();
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  setFullGraphViewport();
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-chorusing-marker-row-0"]')!;
  return { row, svg };
}

export function clickMarkerRail(svg: SVGSVGElement, ratio: number): void {
  const row = document.querySelector<SVGGElement>('[data-testid="aqe-chorusing-marker-row-0"]')!;
  const target = row.getAttribute("aria-hidden") === "true"
    ? document.querySelector<HTMLElement>(".aqe-chorusing-marker-hitbox")!
    : row;
  const EventCtor = window.PointerEvent || window.MouseEvent;
  const clientX = graphClientX(svg, ratio);
  target.dispatchEvent(new EventCtor("pointerdown", {
    bubbles: true,
    clientX,
    clientY: 155,
  }));
  window.dispatchEvent(new EventCtor("pointerup", {
    bubbles: true,
    clientX,
    clientY: 155,
  }));
}

export function dragGraphCursor(svg: SVGSVGElement, ratio: number): void {
  const clientX = graphClientX(svg, ratio);
  dispatchGraphPointer(svg, "pointerdown", clientX);
  dispatchGraphPointer(svg, "pointermove", clientX);
  dispatchGraphPointer(svg, "pointerup", clientX);
}

export async function configureSelectedRepeatAutoAdvance(repeatCount = 2): Promise<HTMLAudioElement> {
  const audio = await configureSelectedRepeatOnly();
  enableSelectedAutoAdvance(repeatCount);
  await flushPlaybackWork();
  return audio;
}

export async function configureSelectedRepeatOnly(): Promise<HTMLAudioElement> {
  const audio = prepareHtmlAudio();
  setRepeatEnabledForOrd(0, true);
  await flushPlaybackWork();
  return audio;
}

export function enableSelectedAutoAdvance(repeatCount = 2): void {
  setChorusingAutoAdvanceForField(0, true);
  setChorusingRepeatCountForField(0, repeatCount);
}

export async function startSelectedPlayback(): Promise<void> {
  playButton().click();
  await flushPlaybackWork();
}

export async function pauseSelectedPlayback(): Promise<void> {
  playButton().click();
  await flushPlaybackWork();
}

export async function forceSelectedPlaybackBoundary(): Promise<void> {
  const state = window.__aqeGraphStateForTest?.(0);
  if (!state) throw new Error("graph state unavailable");
  handlePlaybackBoundary(visualizer(), state.playbackEndMs);
  await flushPlaybackWork();
}

export async function forceAudioEndedBoundary(): Promise<void> {
  const state = window.__aqeGraphStateForTest?.(0);
  const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]');
  if (!state || !audio) throw new Error("graph state or audio clock unavailable");
  audio.currentTime = state.playbackEndMs / 1000;
  audio.dispatchEvent(new Event("ended"));
  await flushPlaybackWork();
}

export async function flushPlaybackWork(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

export function longerSuffixButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-next"]')!;
}

export function shorterSuffixButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-chorusing-previous"]')!;
}

function playButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!;
}

function visualizer(): HTMLElement {
  return document.querySelector('.aqe-visualizer[data-aqe-field-ord="0"]')!;
}
