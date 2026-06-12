import type { EditorFieldState } from "./field-state.js";
import { initialFieldState } from "./field-state.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { syncFieldStateToDom } from "./field-state-dom-sync.js";
import type { VisualizerElement } from "./types.js";

const _fieldStates: Map<number, EditorFieldState> = new Map();

export function initFieldState(ord: number, state?: EditorFieldState): EditorFieldState {
  const resolved = state ?? initialFieldState({ ord });
  _fieldStates.set(ord, resolved);
  syncFieldStateToDom(ord, resolved);
  return resolved;
}

export function readFieldState(ord: number): EditorFieldState {
  const stored = _fieldStates.get(ord);
  if (stored) return stored;
  const initial = initialFieldState({ ord });
  _fieldStates.set(ord, initial);
  return initial;
}

export function invalidateFieldState(ord: number): void {
  _fieldStates.delete(ord);
}

export function setCachedProgressMs(
  ord: number,
  progressMs: number,
  visualizer?: VisualizerElement | null,
): void {
  const rounded = Math.round(progressMs);
  const stored = _fieldStates.get(ord) ?? initialFieldState({ ord });
  _fieldStates.set(ord, {
    ...stored,
    cursor: { ...stored.cursor, progressMs: rounded },
  });
  const target = visualizer ?? visualizerForOrd(ord);
  if (target) {
    target.dataset.progressMs = String(rounded);
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
