import { emptyChorusingState, type ChorusingState } from "./chorusing-state.js";

const states = new Map<number, ChorusingState>();

export function readChorusingState(ord: number): ChorusingState {
  return states.get(ord) ?? emptyChorusingState();
}

export function writeChorusingStateForOrd(ord: number, state: ChorusingState): void {
  states.set(ord, state);
}

export function clearChorusingStates(): void {
  states.clear();
}
