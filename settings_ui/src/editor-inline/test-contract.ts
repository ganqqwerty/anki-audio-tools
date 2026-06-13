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
import { cursorMsFromEvent, graphPixelBounds, svgViewBoxScale } from "./plot.js";
import { chorusingControlsForVisualizer } from "./chorusing-dom.js";
import { applyVisualizerTimeViewport } from "./viewport-actions.js";
import { readVisualizerTargetDurationMs, readVisualizerTimeViewport } from "./visualizer-state.js";
import { readFieldState, updateFieldState, writeFieldState } from "./field-state-store.js";
import type { EditorFieldState } from "./field-state.js";
import type {
  CursorPositionForTest,
  EditorCommand,
  GraphStateForTest,
  PlaybackState,
  ProgressClockMode,
  VisualizerElement,
} from "./types.js";
import { isPlaybackState } from "./types.js";

type GraphBoundsForTest = { left: number; width: number };
type FieldStatePatchForTest = Partial<Omit<EditorFieldState, "cursor" | "graph" | "playback" | "selection">> & {
  cursor?: Partial<EditorFieldState["cursor"]>;
  graph?: Partial<EditorFieldState["graph"]>;
  playback?: Partial<EditorFieldState["playback"]>;
  selection?: Partial<EditorFieldState["selection"]>;
};

export const EDITOR_TEST_WINDOW_CONTRACT_NAMES = [
  "__aqeFieldState",
  "__aqeGraphStateForTest",
  "__aqeGraphPixelBoundsForTest",
  "__aqeInstallAudioPlaybackTestDriverForTest",
  "__aqeSetFieldStateForTest",
  "__aqeSetCursorByClientXForTest",
  "__aqeSetCursorForTest",
  "__aqeSetTimeViewportForTest",
] as const;

export function installEditorTestWindowContract(): void {
  window.__aqeFieldState = readFieldState;
  window.__aqeGraphStateForTest = graphStateForTest;
  window.__aqeGraphPixelBoundsForTest = graphPixelBoundsForTest;
  window.__aqeInstallAudioPlaybackTestDriverForTest = installAudioPlaybackTestDriver;
  window.__aqeSetFieldStateForTest = setFieldStateForTest;
  window.__aqeSetCursorByClientXForTest = setCursorByClientXForTest;
  window.__aqeSetCursorForTest = setCursorForTest;
  window.__aqeSetTimeViewportForTest = setTimeViewportForTest;
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
  updateFieldState(ord, (state) => ({
    ...state,
    graph: { ...state.graph, active: true },
  }));
  setCursor(visualizer, ms, !!notifyPython);
  return true;
}

export function setFieldStateForTest(ord: number, patch: FieldStatePatchForTest): EditorFieldState | null {
  if (!visualizerForOrd(ord)) return null;
  const current = readFieldState(ord);
  const next: EditorFieldState = {
    ...current,
    ...patch,
    cursor: { ...current.cursor, ...patch.cursor },
    graph: { ...current.graph, ...patch.graph },
    playback: { ...current.playback, ...patch.playback },
    selection: { ...current.selection, ...patch.selection },
  };
  writeFieldState(ord, next);
  return next;
}

export function setCursorByClientXForTest(ord: number, clientX: number, notifyPython: boolean): CursorPositionForTest | null {
  const visualizer = visualizerForOrd(ord);
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  if (!visualizer || !svg) return null;
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  const ms = cursorMsFromEvent({ clientX }, svg, durationMs, readVisualizerTimeViewport(visualizer));
  setCursor(visualizer, ms, !!notifyPython);
  return {
    cursorMs: Number(visualizer.dataset.cursorMs || "0"),
    cursorX: cssCursorViewBoxX(visualizer),
    bounds: graphPixelBounds(svg),
  };
}

export function graphPixelBoundsForTest(ord: number): GraphBoundsForTest | null {
  const visualizer = visualizerForOrd(ord);
  const svg = visualizer?.querySelector<SVGSVGElement>(".aqe-visualizer-svg") ?? null;
  if (!svg) return null;
  return graphPixelBounds(svg);
}

export function setTimeViewportForTest(ord: number, startMs: number, endMs: number): boolean {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return false;
  applyVisualizerTimeViewport(visualizer, {
    durationMs: readVisualizerTargetDurationMs(visualizer),
    endMs,
    startMs,
  });
  return true;
}

export function graphStateForTest(ord: number): GraphStateForTest | null {
  const visualizer = visualizerForOrd(ord);
  const graph = graphButton(ord);
  const play = playButton(ord);
  const repeatMenu = controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-play-split-button .aqe-split-menu-button") ?? null;
  const regionDelete = controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-region-button") ?? null;
  const regionDeleteRest = controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-rest-button") ?? null;
  if (!visualizer) return null;
  const buttonIcons = allButtons().flatMap((button) => (
    Array.from(button.querySelectorAll<SVGElement>(".aqe-button-icon svg"))
  ));
  const audio = audioClockFor(visualizer);
  const selection = selectionForVisualizer(visualizer);
  const draftSelection = draftSelectionForVisualizer(visualizer);
  const plot = visualizer.querySelector<HTMLElement>(".aqe-visualizer-plot");
  const startHandle = visualizer.querySelector<HTMLElement>(".aqe-selection-resize-start");
  const endHandle = visualizer.querySelector<HTMLElement>(".aqe-selection-resize-end");
  const selectionToolbar = visualizer.querySelector<HTMLElement>(".aqe-selection-toolbar");
  const selectionToolbarPlay = visualizer.querySelector<HTMLButtonElement>(".aqe-selection-toolbar-play");
  const selectionToolbarPreview = visualizer.dataset.selectionToolbarPreview;
  const cssCursor = visualizer.querySelector<HTMLElement>(".aqe-css-cursor");
  const timecodeFlag = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag");
  const timecodeFlagCurrent = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag-current");
  const timecodeFlagPitch = visualizer.querySelector<HTMLElement>(".aqe-css-cursor-flag-pitch");
  const spinner = visualizer.closest<HTMLElement>(".aqe-controls")?.querySelector<HTMLElement>(".aqe-spinner")
    ?? visualizer.querySelector<HTMLElement>(".aqe-spinner");
  const viewport = readVisualizerTimeViewport(visualizer);
  const chorusing = chorusingControlsForVisualizer(visualizer);
  return {
    active: visualizer.dataset.graphActive === "true",
    busy: visualizer.dataset.graphBusy === "true",
    hidden: !!visualizer.hidden,
    hasTrack: visualizer.dataset.hasTrack === "true",
    durationMs: Number(visualizer.dataset.durationMs || "0"),
    targetDurationMs: readVisualizerTargetDurationMs(visualizer),
    viewportStartMs: viewport.startMs,
    viewportEndMs: viewport.endMs,
    learnerAlignmentOffsetMs: Number(visualizer.dataset.learnerAlignmentOffsetMs || "0"),
    learnerDurationMs: Number(visualizer.dataset.learnerDurationMs || "0"),
    learnerRecordingStatus: visualizer.dataset.learnerRecordingStatus || "idle",
    learnerPlaybackStatus: visualizer.dataset.learnerPlaybackStatus || "stopped",
    learnerStartCursorMs: Number(visualizer.dataset.learnerStartCursorMs || "0"),
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
    selectionStartHandleVisible: startHandle ? !startHandle.hidden : false,
    selectionStartHandleX: selectionHandleLeftPx(plot, "--aqe-selection-start-edge-px"),
    selectionEndHandleVisible: endHandle ? !endHandle.hidden : false,
    selectionEndHandleX: selectionHandleLeftPx(plot, "--aqe-selection-end-edge-px"),
    repeatEnabled: visualizer.dataset.repeatEnabled === "true",
    repeatPauseSeconds: Number(visualizer.dataset.repeatPauseSeconds || "0"),
    repeatPauseWaiting: visualizer.dataset.repeatPauseWaiting === "true",
    repeatControlDisabled: !!(repeatMenu?.disabled || repeatButtonForOrd(ord)?.disabled),
    regionDeleteButtonDisabled: !!regionDelete?.disabled,
    regionDeleteButtonHidden: regionDelete ? !!regionDelete.hidden : true,
    regionDeleteRestButtonDisabled: !!regionDeleteRest?.disabled,
    regionDeleteRestButtonHidden: regionDeleteRest ? !!regionDeleteRest.hidden : true,
    selectionToolbarDeleteRegionDisabled: !!regionDelete?.disabled,
    selectionToolbarDeleteRegionHidden: regionDelete ? !!regionDelete.hidden : true,
    selectionToolbarDeleteRestDisabled: !!regionDeleteRest?.disabled,
    selectionToolbarDeleteRestHidden: regionDeleteRest ? !!regionDeleteRest.hidden : true,
    selectionToolbarHidden: selectionToolbar ? !!selectionToolbar.hidden : true,
    selectionToolbarLeftPx: selectionToolbar ? cssPixelNumber(selectionToolbar.style.left) : null,
    selectionToolbarPlayAriaLabel: selectionToolbarPlay?.getAttribute("aria-label") || "",
    selectionToolbarPlayState: selectionToolbarPlay?.dataset.aqeButtonState === "pause" ? "pause" : "play",
    selectionToolbarPreview: selectionToolbarPreview === "region" || selectionToolbarPreview === "rest"
      ? selectionToolbarPreview
      : "none",
    selectionToolbarTopPx: selectionToolbar ? cssPixelNumber(selectionToolbar.style.top) : null,
    chorusingActiveEndMs: chorusing.activeSuffixEndMs,
    chorusingActiveMarkerIndex: chorusing.activeMarkerIndex,
    chorusingActiveStartMs: chorusing.activeSuffixStartMs,
    chorusingBaseEndMs: chorusing.baseEndMs,
    chorusingBaseStartMs: chorusing.baseStartMs,
    chorusingCanNext: chorusing.canNext,
    chorusingCanPrevious: chorusing.canPrevious,
    chorusingCanPractice: chorusing.canPractice,
    chorusingMarkerVisibleXs: chorusing.visibleMarkers.map((marker) => marker.x),
    chorusingMarkersMs: chorusing.markersMs,
    chorusingState: chorusing.practiceState,
    chorusingVisibleActiveRangeEndX: chorusing.visibleActiveRange?.endX ?? null,
    chorusingVisibleActiveRangeStartX: chorusing.visibleActiveRange?.startX ?? null,
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
    learnerIntensityPaths: visualizer.querySelectorAll(".aqe-learner-intensity-path").length,
    learnerPitchPaths: visualizer.querySelectorAll(".aqe-learner-pitch-path").length,
    intensity: visualizer.querySelector<SVGPathElement>(".aqe-intensity")?.getAttribute("d") || "",
    cursorX: cssCursorViewBoxX(visualizer),
    pitchMarkerVisible: false,
    pitchMarkerX: null,
    pitchMarkerY: null,
    timecodeFlagVisible: cssCursor?.style.display === "block",
    timecodeFlagTransform: cssCursor?.style.transform || timecodeFlag?.style.transform || "",
    timecodeFlagCurrent: timecodeFlagCurrent?.textContent || "",
    timecodeFlagPitch: timecodeFlagPitch?.textContent || "",
    spinnerVisible: spinner ? !spinner.hidden : false,
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

function selectionHandleLeftPx(plot: HTMLElement | null, propertyName: string): number | null {
  const edgePx = cssPixelNumber(plot?.style.getPropertyValue(propertyName).trim() || "");
  return edgePx === null ? null : edgePx - 5;
}

function cssCursorViewBoxX(visualizer: VisualizerElement): number {
  const cursor = visualizer.querySelector<HTMLElement>(".aqe-css-cursor");
  const transform = cursor?.style.transform || "";
  const match = /translate3d\((-?\d+(?:\.\d+)?)px/.exec(transform);
  const x = match ? Number(match[1]) : 0;
  const svg = visualizer.querySelector<SVGSVGElement>(".aqe-visualizer-svg");
  const scale = svg ? svgViewBoxScale(svg).x : 1;
  return x / scale;
}
