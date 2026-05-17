import type { PlaybackState, ProgressClockMode } from "./types.js";
import {
  type PlaybackEngine,
  type PlaybackRegion,
  type PlaybackRegionMode,
} from "./playback-state.js";
import {
  type SelectionState,
  clampMs,
  clearDraftSelectionState,
  clearSelectionState,
  emptySelectionState,
  setDraftSelectionRange,
  setSelectionRange,
} from "./selection-state.js";

export interface EditorFieldState {
  cursor: {
    anchorMs: number;
    ms: number;
    progressMs: number;
  };
  graph: {
    active: boolean;
    analyzerName: string;
    busy: boolean;
    durationMs: number;
    hasTrack: boolean;
  };
  ord: number;
  playback: {
    clockMode: ProgressClockMode;
    engine: PlaybackEngine;
    endMs: number;
    regionMode: PlaybackRegionMode;
    repeat: boolean;
    resumeRequiresRestart: boolean;
    startMs: number;
    state: PlaybackState;
  };
  selection: SelectionState;
  sourceFilename: string;
}

export interface InitialFieldStateInput {
  ord: number;
  repeatByDefault?: boolean;
  sourceFilename?: string;
}

export function initialFieldState(input: InitialFieldStateInput): EditorFieldState {
  return {
    cursor: {
      anchorMs: 0,
      ms: 0,
      progressMs: 0,
    },
    graph: {
      active: false,
      analyzerName: "",
      busy: false,
      durationMs: 0,
      hasTrack: false,
    },
    ord: input.ord,
    playback: {
      clockMode: "stopped",
      engine: "",
      endMs: 0,
      regionMode: "full",
      repeat: input.repeatByDefault === true,
      resumeRequiresRestart: false,
      startMs: 0,
      state: "stopped",
    },
    selection: emptySelectionState(),
    sourceFilename: input.sourceFilename ?? "",
  };
}

export function graphRequested(state: EditorFieldState): EditorFieldState {
  return {
    ...state,
    cursor: {
      anchorMs: 0,
      ms: 0,
      progressMs: 0,
    },
    graph: {
      active: true,
      analyzerName: "",
      busy: true,
      durationMs: 0,
      hasTrack: false,
    },
    playback: {
      ...state.playback,
      clockMode: "stopped",
      engine: "",
      endMs: 0,
      regionMode: "full",
      resumeRequiresRestart: false,
      startMs: 0,
      state: "stopped",
    },
    selection: clearSelectionState(state.selection),
    sourceFilename: "",
  };
}

export function graphRendered(
  state: EditorFieldState,
  payload: {
    analyzerName: string;
    cursorMs: number;
    durationMs: number;
    sourceFilename: string;
  },
): EditorFieldState {
  const durationMs = Math.max(0, Number(payload.durationMs) || 0);
  const cursorMs = clampMs(payload.cursorMs, durationMs);
  return {
    ...state,
    cursor: {
      anchorMs: cursorMs,
      ms: cursorMs,
      progressMs: cursorMs,
    },
    graph: {
      active: true,
      analyzerName: payload.analyzerName || "",
      busy: false,
      durationMs,
      hasTrack: true,
    },
    playback: {
      ...state.playback,
      endMs: durationMs,
      regionMode: "full",
      startMs: 0,
    },
    selection: clearSelectionState(state.selection),
    sourceFilename: payload.sourceFilename || "",
  };
}

export function analyzerStatusChanged(
  state: EditorFieldState,
  status: {
    kind?: string;
  },
): EditorFieldState {
  const processing = status.kind === "processing";
  return {
    ...state,
    graph: {
      ...state.graph,
      active: true,
      busy: processing,
      hasTrack: processing ? false : state.graph.hasTrack,
    },
  };
}

export function cursorMoved(state: EditorFieldState, ms: number, options: { updateAnchor?: boolean } = {}): EditorFieldState {
  const cursorMs = clampMs(ms, state.graph.durationMs);
  return {
    ...state,
    cursor: {
      anchorMs: options.updateAnchor === false ? state.cursor.anchorMs : cursorMs,
      ms: cursorMs,
      progressMs: cursorMs,
    },
  };
}

export function selectionDraftChanged(state: EditorFieldState, startMs: number, endMs: number): EditorFieldState {
  return {
    ...state,
    selection: setDraftSelectionRange(state.selection, startMs, endMs, state.graph.durationMs),
  };
}

export function selectionCommitted(state: EditorFieldState, startMs: number, endMs: number): EditorFieldState {
  const selection = setSelectionRange(state.selection, startMs, endMs, state.graph.durationMs);
  if (!selection.active || selection.startMs === null || selection.endMs === null) {
    return {
      ...state,
      selection,
      playback: fullPlaybackRegion(state),
    };
  }
  return {
    ...cursorMoved(state, selection.startMs),
    playback: {
      ...state.playback,
      endMs: selection.endMs,
      regionMode: "selection",
      startMs: selection.startMs,
    },
    selection,
  };
}

export function draftSelectionCommitted(state: EditorFieldState): EditorFieldState {
  if (!state.selection.draftActive || state.selection.draftStartMs === null || state.selection.draftEndMs === null) {
    return {
      ...state,
      selection: clearDraftSelectionState(state.selection),
    };
  }
  return selectionCommitted(state, state.selection.draftStartMs, state.selection.draftEndMs);
}

export function selectionCleared(state: EditorFieldState): EditorFieldState {
  return {
    ...state,
    playback: fullPlaybackRegion(state),
    selection: clearSelectionState(state.selection),
  };
}

export function repeatToggled(state: EditorFieldState, enabled: boolean): EditorFieldState {
  return {
    ...state,
    playback: {
      ...state.playback,
      repeat: enabled,
    },
  };
}

export function playbackStarted(
  state: EditorFieldState,
  startMs: number,
  options: { clockMode?: ProgressClockMode; engine?: PlaybackEngine } = {},
): EditorFieldState {
  const region = effectivePlaybackRegion(state);
  const clampedStartMs = clampMsToPlaybackRegion(startMs, region);
  return {
    ...cursorMoved(state, clampedStartMs, { updateAnchor: false }),
    playback: {
      ...state.playback,
      clockMode: options.clockMode ?? state.playback.clockMode,
      engine: options.engine ?? state.playback.engine,
      endMs: region.endMs,
      regionMode: region.mode,
      resumeRequiresRestart: false,
      startMs: clampedStartMs,
      state: "playing",
    },
  };
}

export function playbackPaused(state: EditorFieldState, cursorMs: number): EditorFieldState {
  return {
    ...cursorMoved(state, cursorMs, { updateAnchor: false }),
    playback: {
      ...state.playback,
      clockMode: "stopped",
      state: "paused",
    },
  };
}

export function playbackStopped(state: EditorFieldState, options: { clearEngine?: boolean } = {}): EditorFieldState {
  return {
    ...state,
    playback: {
      ...state.playback,
      clockMode: "stopped",
      engine: options.clearEngine === false ? state.playback.engine : "",
      resumeRequiresRestart: false,
      state: "stopped",
    },
  };
}

export function resetForNewNote(state: EditorFieldState, repeatByDefault = state.playback.repeat): EditorFieldState {
  return initialFieldState({
    ord: state.ord,
    repeatByDefault,
  });
}

export function effectivePlaybackRegion(state: EditorFieldState): PlaybackRegion {
  if (state.selection.active && state.selection.startMs !== null && state.selection.endMs !== null) {
    return {
      startMs: state.selection.startMs,
      endMs: state.selection.endMs,
      mode: "selection",
    };
  }
  return {
    startMs: 0,
    endMs: state.graph.durationMs,
    mode: "full",
  };
}

function fullPlaybackRegion(state: EditorFieldState): EditorFieldState["playback"] {
  return {
    ...state.playback,
    endMs: state.graph.durationMs,
    regionMode: "full",
    startMs: 0,
  };
}

function clampMsToPlaybackRegion(ms: number, region: Pick<PlaybackRegion, "endMs" | "startMs">): number {
  return Math.max(region.startMs, Math.min(Number(ms) || 0, region.endMs));
}
