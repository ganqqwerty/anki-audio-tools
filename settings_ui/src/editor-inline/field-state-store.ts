import type { EditorFieldState } from "./field-state.js";
import { initialFieldState } from "./field-state.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { syncFieldStateToDom } from "./field-state-dom-sync.js";
import type { ProgressClockMode } from "./types.js";
import type { PlaybackEngine, PlaybackRegionMode } from "./playback-state.js";
import type { SelectionState } from "./selection-state.js";

const _fieldStates: Map<number, EditorFieldState> = new Map();

function readVisualizerSelectionStateFromDom(visualizer: HTMLElement): SelectionState {
  return {
    active: visualizer.dataset.selectionActive === "true",
    draftActive: visualizer.dataset.selectionDraftActive === "true",
    draftEndMs: readOptionalMs(visualizer.dataset.selectionDraftEndMs),
    draftStartMs: readOptionalMs(visualizer.dataset.selectionDraftStartMs),
    endMs: readOptionalMs(visualizer.dataset.selectionEndMs),
    startMs: readOptionalMs(visualizer.dataset.selectionStartMs),
  };
}

function readOptionalMs(rawValue: string | undefined): number | null {
  if (!rawValue) return null;
  const value = Number(rawValue);
  return Number.isFinite(value) ? value : null;
}

function targetDurationMsFromDom(visualizer: HTMLElement): number {
  const targetDurationMs = Number(visualizer.dataset.targetDurationMs || "0") || 0;
  if (targetDurationMs > 0) return targetDurationMs;
  return Number(visualizer.dataset.durationMs || "0") || 0;
}

function rebuildFieldStateFromDom(ord: number): EditorFieldState {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) {
    return initialFieldState({ ord });
  }
  return {
    cursor: {
      anchorMs: Number(visualizer.dataset.anchorMs || "0") || 0,
      ms: Number(visualizer.dataset.cursorMs || "0") || 0,
      progressMs: Number(visualizer.dataset.progressMs || "0") || 0,
    },
    graph: {
      active: visualizer.dataset.graphActive === "true",
      analyzerName: visualizer.dataset.analyzerName || "",
      busy: visualizer.dataset.graphBusy === "true",
      durationMs: Number(visualizer.dataset.durationMs || "0") || 0,
      hasTrack: visualizer.dataset.hasTrack === "true",
    },
    ord,
    playback: {
      clockMode: playbackClockModeForDataset(visualizer.dataset.progressClockMode),
      engine: playbackEngineForDataset(visualizer.dataset.playbackEngine),
      endMs: readStoredMs(visualizer.dataset.playbackEndMs, targetDurationMsFromDom(visualizer)),
      regionMode: playbackRegionModeForDataset(visualizer.dataset.playbackRegionMode),
      repeat: visualizer.dataset.repeatEnabled === "true",
      resumeRequiresRestart: visualizer.dataset.resumeRequiresRestart === "true",
      startMs: readStoredMs(visualizer.dataset.playbackStartMs, 0),
      state: playbackStateForDataset(visualizer.dataset.playbackState),
    },
    selection: readVisualizerSelectionStateFromDom(visualizer),
    sourceFilename: visualizer.dataset.sourceFilename || "",
  };
}

export function initFieldState(ord: number, state?: EditorFieldState): EditorFieldState {
  const resolved = state ?? initialFieldState({ ord });
  _fieldStates.set(ord, resolved);
  syncFieldStateToDom(ord, resolved);
  return resolved;
}

export function readFieldState(ord: number): EditorFieldState {
  const stored = _fieldStates.get(ord);
  if (stored) return stored;
  const rebuilt = rebuildFieldStateFromDom(ord);
  _fieldStates.set(ord, rebuilt);
  return rebuilt;
}

export function invalidateFieldState(ord: number): void {
  _fieldStates.delete(ord);
}

export function setCachedProgressMs(ord: number, progressMs: number): void {
  const rounded = Math.round(progressMs);
  const stored = _fieldStates.get(ord);
  if (stored) {
    _fieldStates.set(ord, {
      ...stored,
      cursor: { ...stored.cursor, progressMs: rounded },
    });
  }
  const visualizer = visualizerForOrd(ord);
  if (visualizer) {
    visualizer.dataset.progressMs = String(rounded);
  }
}

export function writeFieldState(ord: number, state: EditorFieldState): void {
  _fieldStates.set(ord, { ...state });
  syncFieldStateToDom(ord, state);
}

export function updateFieldState(
  ord: number,
  reducer: (state: EditorFieldState) => EditorFieldState,
): EditorFieldState {
  const next = reducer(readFieldState(ord));
  writeFieldState(ord, next);
  return next;
}

export function removeFieldState(ord: number): void {
  _fieldStates.delete(ord);
}

export function hasFieldState(ord: number): boolean {
  return _fieldStates.has(ord);
}

function playbackStateForDataset(value: string | undefined): EditorFieldState["playback"]["state"] {
  if (value === "playing" || value === "paused") return value;
  return "stopped";
}

function playbackClockModeForDataset(value: string | undefined): ProgressClockMode {
  if (value === "audio" || value === "manual") return value;
  return "stopped";
}

function playbackEngineForDataset(value: string | undefined): PlaybackEngine {
  return value === "html" || value === "native" ? value : "";
}

function playbackRegionModeForDataset(value: string | undefined): PlaybackRegionMode {
  return value === "selection" ? "selection" : "full";
}

function readStoredMs(rawValue: string | undefined, fallbackMs: number): number {
  if (!rawValue) return fallbackMs;
  const value = Number(rawValue);
  return Number.isFinite(value) ? value : fallbackMs;
}
