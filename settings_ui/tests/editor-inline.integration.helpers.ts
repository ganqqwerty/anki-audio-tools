import { vi } from "vitest";

import { pycmdMock } from "./setup.js";

export const track = {
  analyzerName: "praat",
  durationMs: 1000,
  pitchMaxHz: 300,
  pitchMinHz: 100,
  points: [
    [0, 120, 0.1, true],
    [200, 180, 0.8, true],
    [400, null, 0, false],
    [600, 260, 0.4, true],
    [1000, 280, 1, true],
  ],
  sourceFilename: "clip one.mp3",
};

export function commandLog(): string[] {
  return pycmdMock.mock.calls.map(([command]) => command);
}

export function bridgeCommands(): string[] {
  return commandLog().filter((command) => command.startsWith("focus:") || command.startsWith("aqe:"));
}

export function renderFields(): void {
  document.body.innerHTML = `
    <div class="field-container" data-index="0">
      <div contenteditable="true" id="f0">[sound:clip one.mp3]</div>
    </div>
    <div class="field-container" data-index="1">
      <div contenteditable="true" id="f1">plain text</div>
    </div>
  `;
}

export function renderTwoAudioFields(): void {
  document.body.innerHTML = `
    <div class="field-container" data-index="0">
      <div contenteditable="true" id="f0">[sound:clip one.mp3]</div>
    </div>
    <div class="field-container" data-index="1">
      <div contenteditable="true" id="f1">[sound:clip two.mp3]</div>
    </div>
  `;
}

export function graphClientX(svg: SVGSVGElement, ratio: number): number {
  const rect = svg.getBoundingClientRect();
  return 44 + 566 * ratio + rect.left;
}

export function dispatchGraphPointer(svg: SVGSVGElement, type: string, clientX: number, shiftKey = false): void {
  const EventCtor = window.PointerEvent || window.MouseEvent;
  const rect = svg.getBoundingClientRect();
  const event = new EventCtor(type, {
    bubbles: true,
    clientX,
    clientY: rect.top + 20,
    shiftKey,
  });
  if (type === "pointerdown") {
    svg.dispatchEvent(event);
    return;
  }
  window.dispatchEvent(event);
}

export function dragGraphSelection(svg: SVGSVGElement, startRatio: number, endRatio: number): void {
  dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, startRatio), true);
  dispatchGraphPointer(svg, "pointermove", graphClientX(svg, endRatio), true);
  dispatchGraphPointer(svg, "pointerup", graphClientX(svg, endRatio), true);
}

export function dispatchHandlePointer(handle: Element, type: string, clientX: number, shiftKey = false): void {
  const EventCtor = window.PointerEvent || window.MouseEvent;
  const event = new EventCtor(type, {
    bubbles: true,
    clientX,
    clientY: 20,
    shiftKey,
  });
  if (type === "pointerdown") {
    handle.dispatchEvent(event);
    return;
  }
  window.dispatchEvent(event);
}

export function dragSelectionHandle(svg: SVGSVGElement, edge: "end" | "start", endRatio: number, ord = 0): void {
  const handle = document.querySelector(`[data-testid="aqe-selection-resize-${edge}-${ord}"]`)!;
  dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, edge === "start" ? 0.2 : 0.6));
  dispatchHandlePointer(handle, "pointermove", graphClientX(svg, endRatio));
  dispatchHandlePointer(handle, "pointerup", graphClientX(svg, endRatio));
}

export function selectionToolbarButton(
  kind: "collapse" | "delete-region" | "delete-rest" | "play",
  ord = 0,
): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>(`[data-testid="aqe-selection-toolbar-${kind}-${ord}"]`)!;
}

export function selectionToolbarDot(ord = 0): SVGSVGElement {
  return document.querySelector<SVGSVGElement>(`[data-testid="aqe-selection-toolbar-dot-${ord}"]`)!;
}

export function hoverToolbarButton(button: HTMLElement): void {
  button.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
}

export function leaveToolbarButton(button: HTMLElement): void {
  button.dispatchEvent(new MouseEvent("mouseleave", { bubbles: true }));
}

export function setGraphBounds(
  svg: SVGSVGElement,
  bounds: Partial<{ height: number; left: number; top: number; width: number }> = {},
): void {
  const height = bounds.height ?? 150;
  const left = bounds.left ?? 0;
  const top = bounds.top ?? 0;
  const width = bounds.width ?? 620;
  svg.getBoundingClientRect = () => ({
    bottom: top + height,
    height,
    left,
    right: left + width,
    top,
    width,
    x: left,
    y: top,
    toJSON: () => ({}),
  });
}

export function prepareHtmlAudio(ord = 0): HTMLAudioElement {
  const audio = document.querySelector<HTMLAudioElement>(`[data-testid="aqe-audio-clock-${ord}"]`)!;
  Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
  audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
  audio.pause = vi.fn<() => void>(() => undefined);
  audio.dispatchEvent(new Event("loadedmetadata"));
  return audio;
}

export async function openPlayOptions(ord = 0): Promise<void> {
  const menu = document.querySelector<HTMLButtonElement>(`[data-testid="aqe-split-${ord}-play-menu"]`)!;
  if (menu.getAttribute("aria-expanded") !== "true") {
    menu.click();
    await Promise.resolve();
  }
}

export async function setRepeatMode(enabled: boolean, ord = 0): Promise<HTMLButtonElement> {
  await openPlayOptions(ord);
  const repeat = document.querySelector<HTMLButtonElement>(`[data-testid="aqe-repeat-${ord}"]`)!;
  if ((repeat.getAttribute("aria-pressed") === "true") !== enabled) {
    repeat.click();
    await Promise.resolve();
  }
  const menu = document.querySelector<HTMLButtonElement>(`[data-testid="aqe-split-${ord}-play-menu"]`)!;
  if (menu.getAttribute("aria-expanded") === "true") {
    menu.click();
    await Promise.resolve();
  }
  return repeat;
}

export function clearQueuedAnimationFrames(
  frames: Array<Parameters<typeof window.requestAnimationFrame>[0]>,
): void {
  frames.length = 0;
}

export function mockAnimationFrames(): Array<Parameters<typeof window.requestAnimationFrame>[0]> {
  const frames: Array<Parameters<typeof window.requestAnimationFrame>[0]> = [];
  vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
    frames.push(callback);
    return frames.length;
  });
  vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
  return frames;
}

export function muteConsole(): () => void {
  const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
  const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  return () => {
    warnSpy.mockRestore();
    errorSpy.mockRestore();
  };
}
