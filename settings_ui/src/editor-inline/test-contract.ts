import { COMMAND_SLUGS } from "./commands.js";
import { audioClockFor } from "./audio-clock.js";
import {
  allButtons,
  controlsForOrd,
  graphButton,
  playButton,
  repeatButtonForOrd,
  visualizerForOrd,
} from "./dom-selectors.js";
import {
  currentProgressMs,
  draftSelectionForVisualizer,
  playbackEngineFor,
  selectionForVisualizer,
  setCursor,
} from "./actions.js";
import { cursorMsFromEvent, graphPixelBounds } from "./plot.js";
import type {
  CursorPositionForTest,
  EditorCommand,
  GraphStateForTest,
  PlaybackState,
  ProgressClockMode,
  VisualizerElement,
} from "./types.js";
import { isPlaybackState } from "./types.js";

export const EDITOR_TEST_WINDOW_CONTRACT_NAMES = [
  "__aqeGraphStateForTest",
  "__aqeInstallAudioPlaybackTestDriverForTest",
  "__aqeSetCursorByClientXForTest",
  "__aqeSetCursorForTest",
] as const;

export function installEditorTestWindowContract(): void {
  window.__aqeGraphStateForTest = graphStateForTest;
  window.__aqeInstallAudioPlaybackTestDriverForTest = installAudioPlaybackTestDriver;
  window.__aqeSetCursorByClientXForTest = setCursorByClientXForTest;
  window.__aqeSetCursorForTest = setCursorForTest;
}

export function installAudioPlaybackTestDriver(ord: number): boolean {
  const visualizer = visualizerForOrd(ord);
  const audio = audioClockFor(visualizer);
  if (!visualizer || !audio) return false;
  const markReady = (): void => {
    try {
      Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
      Object.defineProperty(audio, "duration", {
        configurable: true,
        get: () => Number(visualizer.dataset.durationMs || "0") / 1000,
      });
    } catch {
      // Some browser engines expose media properties as non-configurable.
    }
    visualizer.__aqeAudioClockAvailable = true;
    visualizer.__aqeAudioClockFallback = false;
  };
  audio.__aqeTestDriverInstalled = true;
  markReady();
  audio.addEventListener("error", markReady);
  audio.dispatchEvent(new Event("loadedmetadata"));
  audio.pause = function pause(): void {
    audio.__aqeTestPlaying = false;
    if (audio.__aqeTestFrame) {
      window.cancelAnimationFrame(audio.__aqeTestFrame);
      audio.__aqeTestFrame = null;
    }
  };
  audio.play = function play(): Promise<void> {
    audio.__aqeTestPlaying = true;
    audio.__aqeTestLastNow = performance.now();
    const tick = (): void => {
      if (!audio.__aqeTestPlaying) return;
      const now = performance.now();
      const durationSeconds = Number(visualizer.dataset.durationMs || "0") / 1000;
      const elapsedSeconds = Math.max(0, (now - Number(audio.__aqeTestLastNow || now)) / 1000);
      audio.__aqeTestLastNow = now;
      audio.currentTime = Math.min(durationSeconds, (Number(audio.currentTime) || 0) + elapsedSeconds);
      if (durationSeconds && audio.currentTime >= durationSeconds) {
        audio.__aqeTestPlaying = false;
        audio.dispatchEvent(new Event("ended"));
        return;
      }
      audio.__aqeTestFrame = window.requestAnimationFrame(tick);
    };
    audio.__aqeTestFrame = window.requestAnimationFrame(tick);
    return Promise.resolve();
  };
  return true;
}

export function setCursorForTest(ord: number, ms: number, notifyPython: boolean): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  visualizer.hidden = false;
  visualizer.dataset.graphActive = "true";
  setCursor(visualizer, ms, !!notifyPython);
  return true;
}

export function setCursorByClientXForTest(ord: number, clientX: number, notifyPython: boolean): CursorPositionForTest | null {
  const visualizer = visualizerForOrd(ord);
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  if (!visualizer || !svg) return null;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const ms = cursorMsFromEvent({ clientX }, svg, durationMs);
  setCursor(visualizer, ms, !!notifyPython);
  return {
    cursorMs: Number(visualizer.dataset.cursorMs || "0"),
    cursorX: Number(visualizer.querySelector<SVGLineElement>(".aqe-cursor")?.getAttribute("x1") || "0"),
    bounds: graphPixelBounds(svg),
  };
}

export function graphStateForTest(ord: number): GraphStateForTest | null {
  const visualizer = visualizerForOrd(ord);
  const graph = graphButton(ord);
  const play = playButton(ord);
  const repeatMenu = controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-play-repeat-menu-button") ?? null;
  const regionDelete = controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-region-button") ?? null;
  const regionDeleteRest = controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-rest-button") ?? null;
  if (!visualizer) return null;
  const buttonIcons = allButtons().flatMap((button) => (
    Array.from(button.querySelectorAll<SVGElement>(".aqe-button-icon svg"))
  ));
  const audio = audioClockFor(visualizer);
  const selection = selectionForVisualizer(visualizer);
  const draftSelection = draftSelectionForVisualizer(visualizer);
  const startHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-start");
  const endHandle = visualizer.querySelector<SVGRectElement>(".aqe-selection-resize-end");
  const selectionToolbar = visualizer.querySelector<HTMLElement>(".aqe-selection-toolbar");
  const selectionToolbarDot = visualizer.querySelector<SVGSVGElement>(".aqe-selection-toolbar-dot");
  const selectionToolbarPlay = visualizer.querySelector<HTMLButtonElement>(".aqe-selection-toolbar-play");
  const selectionToolbarPreview = visualizer.dataset.selectionToolbarPreview;
  const timecodeFlag = visualizer.querySelector<SVGGElement>(".aqe-cursor-flag");
  const timecodeFlagCurrent = visualizer.querySelector<SVGTextElement>(".aqe-cursor-flag-current");
  const timecodeFlagPitch = visualizer.querySelector<SVGTextElement>(".aqe-cursor-flag-pitch");
  const pitchMarker = visualizer.querySelector<SVGCircleElement>(".aqe-cursor-pitch-marker");
  return {
    active: visualizer.dataset.graphActive === "true",
    busy: visualizer.dataset.graphBusy === "true",
    hidden: !!visualizer.hidden,
    hasTrack: visualizer.dataset.hasTrack === "true",
    durationMs: Number(visualizer.dataset.durationMs || "0"),
    anchorMs: Number(visualizer.dataset.anchorMs || "0"),
    cursorMs: Number(visualizer.dataset.cursorMs || "0"),
    progressMs: Math.round(currentProgressMs(visualizer) ?? Number(visualizer.dataset.progressMs || "0")),
    sourceFilename: visualizer.dataset.sourceFilename || "",
    graphButtonLabel: buttonLabel(graph),
    graphButtonState: graph?.dataset.aqeButtonState || "",
    graphButtonTitle: graph?.getAttribute("data-aqe-tooltip-content") || "",
    playButtonLabel: buttonLabel(play),
    playButtonState: play?.dataset.aqeButtonState || "",
    playbackState: playbackStateFor(visualizer),
    selectionActive: selection !== null,
    selectionStartMs: selection?.startMs ?? null,
    selectionEndMs: selection?.endMs ?? null,
    selectionDraftActive: draftSelection !== null,
    selectionDraftStartMs: draftSelection?.startMs ?? null,
    selectionDraftEndMs: draftSelection?.endMs ?? null,
    selectionStartHandleVisible: startHandle?.getAttribute("visibility") === "visible",
    selectionStartHandleX: startHandle?.getAttribute("x") ? Number(startHandle.getAttribute("x")) : null,
    selectionEndHandleVisible: endHandle?.getAttribute("visibility") === "visible",
    selectionEndHandleX: endHandle?.getAttribute("x") ? Number(endHandle.getAttribute("x")) : null,
    repeatEnabled: visualizer.dataset.repeatEnabled === "true",
    repeatPauseSeconds: Number(visualizer.dataset.repeatPauseSeconds || "0"),
    repeatPauseWaiting: visualizer.dataset.repeatPauseWaiting === "true",
    repeatControlDisabled: !!(repeatMenu?.disabled || repeatButtonForOrd(ord)?.disabled),
    regionDeleteButtonDisabled: !!regionDelete?.disabled,
    regionDeleteButtonHidden: regionDelete ? !!regionDelete.hidden : true,
    regionDeleteRestButtonDisabled: !!regionDeleteRest?.disabled,
    regionDeleteRestButtonHidden: regionDeleteRest ? !!regionDeleteRest.hidden : true,
    selectionToolbarCollapsed: visualizer.dataset.selectionToolbarCollapsed === "true",
    selectionToolbarDeleteRegionDisabled: !!regionDelete?.disabled,
    selectionToolbarDeleteRegionHidden: regionDelete ? !!regionDelete.hidden : true,
    selectionToolbarDeleteRestDisabled: !!regionDeleteRest?.disabled,
    selectionToolbarDeleteRestHidden: regionDeleteRest ? !!regionDeleteRest.hidden : true,
    selectionToolbarDotHidden: selectionToolbarDot
      ? selectionToolbarDot.hasAttribute("hidden") || selectionToolbarDot.getAttribute("aria-hidden") === "true"
      : true,
    selectionToolbarHidden: selectionToolbar ? !!selectionToolbar.hidden : true,
    selectionToolbarLeftPx: selectionToolbar ? cssPixelNumber(selectionToolbar.style.left) : null,
    selectionToolbarPlayAriaLabel: selectionToolbarPlay?.getAttribute("aria-label") || "",
    selectionToolbarPlayState: selectionToolbarPlay?.dataset.aqeButtonState === "pause" ? "pause" : "play",
    selectionToolbarPreview: selectionToolbarPreview === "region" || selectionToolbarPreview === "rest"
      ? selectionToolbarPreview
      : "none",
    selectionToolbarTopPx: selectionToolbar ? cssPixelNumber(selectionToolbar.style.top) : null,
    playbackStartMs: Number(visualizer.dataset.playbackStartMs || "0"),
    playbackEndMs: Number(visualizer.dataset.playbackEndMs || "0"),
    playbackRegionMode: visualizer.dataset.playbackRegionMode === "selection" ? "selection" : "full",
    resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
    audioClockSrc: audio ? (audio.getAttribute("src") || "") : "",
    audioClockCurrentMs: audio ? Math.round((Number(audio.currentTime) || 0) * 1000) : 0,
    audioClockReady: !!(audio && visualizer.__aqeAudioClockAvailable),
    audioClockFallback: !!visualizer.__aqeAudioClockFallback,
    audioClockMuted: !!(audio && audio.muted),
    audioPlaybackTestDriver: !!(audio && audio.__aqeTestDriverInstalled),
    playbackEngine: playbackEngineFor(visualizer),
    progressClockMode: progressClockModeFor(visualizer),
    xAxisLabels: Array.from(visualizer.querySelectorAll<SVGTextElement>(".aqe-x-label")).map((node) => node.textContent || ""),
    pitchPaths: visualizer.querySelectorAll(".aqe-pitch-path").length,
    intensity: visualizer.querySelector<SVGPathElement>(".aqe-intensity")?.getAttribute("d") || "",
    cursorX: Number(visualizer.querySelector<SVGLineElement>(".aqe-cursor")?.getAttribute("x1") || "0"),
    pitchMarkerVisible: pitchMarker?.getAttribute("visibility") === "visible",
    pitchMarkerX: pitchMarker?.getAttribute("cx") ? Number(pitchMarker.getAttribute("cx")) : null,
    pitchMarkerY: pitchMarker?.getAttribute("cy") ? Number(pitchMarker.getAttribute("cy")) : null,
    timecodeFlagVisible: timecodeFlag?.getAttribute("visibility") === "visible",
    timecodeFlagTransform: timecodeFlag?.getAttribute("transform") || "",
    timecodeFlagCurrent: timecodeFlagCurrent?.textContent || "",
    timecodeFlagPitch: timecodeFlagPitch?.textContent || "",
    spinnerVisible: visualizer.querySelector<HTMLElement>(".aqe-spinner") ? !visualizer.querySelector<HTMLElement>(".aqe-spinner")?.hidden : false,
    allButtonsDisabled: allButtons().every((button) => button.disabled),
    anyButtonDisabled: allButtons().some((button) => button.disabled),
    buttonIconCount: buttonIcons.length,
    buttonIconStrokeValues: buttonIcons.map((node) => node.getAttribute("stroke") || getComputedStyle(node).stroke || ""),
  };
}

export function commandSlugsForTest(): Readonly<Record<EditorCommand, string>> {
  return COMMAND_SLUGS;
}

function playbackStateFor(visualizer: VisualizerElement): PlaybackState {
  const state = visualizer.dataset.playbackState;
  return isPlaybackState(state) ? state : "stopped";
}

function progressClockModeFor(visualizer: VisualizerElement): ProgressClockMode {
  const mode = visualizer.dataset.progressClockMode;
  if (mode === "audio" || mode === "manual" || mode === "stopped") return mode;
  return "stopped";
}

function buttonLabel(button: HTMLButtonElement | null): string {
  return button?.querySelector<HTMLElement>(".aqe-button-label")?.textContent || button?.textContent || "";
}

function cssPixelNumber(value: string): number | null {
  if (!value.endsWith("px")) return null;
  const parsed = Number(value.slice(0, -2));
  return Number.isFinite(parsed) ? parsed : null;
}
