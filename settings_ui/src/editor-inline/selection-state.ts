export const MIN_SELECTION_DURATION_MS = 50;
export const SELECTION_DRAG_PIXEL_THRESHOLD = 4;

export interface SelectionRange {
  endMs: number;
  startMs: number;
}

export interface SelectionState {
  active: boolean;
  draftActive: boolean;
  draftEndMs: number | null;
  draftStartMs: number | null;
  endMs: number | null;
  startMs: number | null;
}

export interface SelectionRegion extends SelectionRange {
  mode: "selection";
}

export function emptySelectionState(): SelectionState {
  return {
    active: false,
    draftActive: false,
    draftEndMs: null,
    draftStartMs: null,
    endMs: null,
    startMs: null,
  };
}

export function clampMs(ms: number, durationMs: number): number {
  return Math.max(0, Math.min(Number(ms) || 0, Math.max(0, Number(durationMs) || 0)));
}

export function normalizeSelectionRange(
  startMs: number,
  endMs: number,
  durationMs: number,
  minDurationMs = MIN_SELECTION_DURATION_MS,
): SelectionRange | null {
  const start = clampMs(Math.min(startMs, endMs), durationMs);
  const end = clampMs(Math.max(startMs, endMs), durationMs);
  if (!durationMs || end - start < minDurationMs) return null;
  return {
    startMs: Math.round(start),
    endMs: Math.round(end),
  };
}

export function selectionRegion(
  state: Pick<SelectionState, "active" | "endMs" | "startMs">,
  durationMs: number,
): SelectionRegion | null {
  if (!state.active || state.startMs === null || state.endMs === null) return null;
  const range = normalizeSelectionRange(state.startMs, state.endMs, durationMs);
  return range ? { ...range, mode: "selection" } : null;
}

export function draftSelectionRegion(
  state: Pick<SelectionState, "draftActive" | "draftEndMs" | "draftStartMs">,
  durationMs: number,
): SelectionRegion | null {
  if (!state.draftActive || state.draftStartMs === null || state.draftEndMs === null) return null;
  const range = normalizeSelectionRange(state.draftStartMs, state.draftEndMs, durationMs);
  return range ? { ...range, mode: "selection" } : null;
}

export function setSelectionRange(
  state: SelectionState,
  startMs: number,
  endMs: number,
  durationMs: number,
): SelectionState {
  const range = normalizeSelectionRange(startMs, endMs, durationMs);
  if (!range) return clearSelectionState(state);
  return {
    ...state,
    active: true,
    draftActive: false,
    draftEndMs: null,
    draftStartMs: null,
    endMs: range.endMs,
    startMs: range.startMs,
  };
}

export function setDraftSelectionRange(
  state: SelectionState,
  startMs: number,
  endMs: number,
  durationMs: number,
): SelectionState {
  const range = normalizeSelectionRange(startMs, endMs, durationMs);
  if (!range) return clearDraftSelectionState(state);
  return {
    ...state,
    draftActive: true,
    draftEndMs: range.endMs,
    draftStartMs: range.startMs,
  };
}

export function commitDraftSelectionState(state: SelectionState, durationMs: number): SelectionState {
  const draft = draftSelectionRegion(state, durationMs);
  if (!draft) return clearDraftSelectionState(state);
  return setSelectionRange(state, draft.startMs, draft.endMs, durationMs);
}

export function clearSelectionState(state: SelectionState): SelectionState {
  return {
    ...clearDraftSelectionState(state),
    active: false,
    endMs: null,
    startMs: null,
  };
}

export function clearDraftSelectionState(state: SelectionState): SelectionState {
  return {
    ...state,
    draftActive: false,
    draftEndMs: null,
    draftStartMs: null,
  };
}

export function shouldTreatSelectionGestureAsClick(
  startEvent: Pick<PointerEvent, "clientX">,
  endEvent: Pick<PointerEvent, "clientX">,
  startMs: number,
  endMs: number,
): boolean {
  return Math.abs(endEvent.clientX - startEvent.clientX) < SELECTION_DRAG_PIXEL_THRESHOLD
    || Math.abs(endMs - startMs) < MIN_SELECTION_DURATION_MS;
}
