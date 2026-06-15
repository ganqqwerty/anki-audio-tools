import type { UserFacingError } from "../lib/user-facing-error.js";
import type { HistorySnapshot } from "./types.js";

export type StatusOwner = "edit" | "error" | "graph" | "playback";
export type EditorStatusMessage = string | UserFacingError;

export interface StoredEditorStatus {
  command: string;
  kind: string;
  message: EditorStatusMessage;
  owner: StatusOwner;
}

interface FieldControlState {
  currentStatus: StoredEditorStatus;
  historySnapshot: HistorySnapshot;
  stableStatus: StoredEditorStatus;
}

const fieldControls: Map<number, FieldControlState> = new Map();
let editorBusy = false;

export function emptyHistorySnapshot(): HistorySnapshot {
  return { canRedo: false, canUndo: false, redoItems: [], undoItems: [] };
}

function emptyStatus(): StoredEditorStatus {
  return {
    command: "",
    kind: "info",
    message: "",
    owner: "edit",
  };
}

function defaultStatusOwner(kind: string): StatusOwner {
  if (kind === "error") return "error";
  if (kind === "processing") return "graph";
  return "edit";
}

function storesStableStatus(owner: StatusOwner): boolean {
  return owner === "edit" || owner === "error";
}

function controlStateFor(ord: number): FieldControlState {
  const existing = fieldControls.get(ord);
  if (existing) return existing;
  const initial = {
    currentStatus: emptyStatus(),
    historySnapshot: emptyHistorySnapshot(),
    stableStatus: emptyStatus(),
  };
  fieldControls.set(ord, initial);
  return initial;
}

export function resetEditorControlState(): void {
  editorBusy = false;
  fieldControls.clear();
}

export function isEditorBusy(): boolean {
  return editorBusy;
}

export function setEditorBusy(busy: boolean): boolean {
  editorBusy = busy;
  return editorBusy;
}

export function setStatusState(
  ord: number,
  message: EditorStatusMessage,
  kind = "info",
  command = "",
  owner: StatusOwner = defaultStatusOwner(kind),
): StoredEditorStatus {
  const state = controlStateFor(ord);
  const next: StoredEditorStatus = {
    command: command || "",
    kind: kind || "info",
    message: message || "",
    owner,
  };
  state.currentStatus = next;
  if (storesStableStatus(owner)) {
    state.stableStatus = next;
  }
  return next;
}

export function setTransientStatusState(
  ord: number,
  message: EditorStatusMessage,
  kind = "info",
  owner: StatusOwner = "graph",
): StoredEditorStatus {
  return setStatusState(ord, message, kind, "", owner);
}

export function clearStatusState(ord: number): StoredEditorStatus {
  const state = controlStateFor(ord);
  state.stableStatus = emptyStatus();
  state.currentStatus = emptyStatus();
  return state.currentStatus;
}

export function restoreStableStatusState(ord: number): StoredEditorStatus {
  const state = controlStateFor(ord);
  const stable = state.stableStatus;
  const restored = {
    ...stable,
    owner: defaultStatusOwner(stable.kind),
  };
  state.currentStatus = restored;
  return restored;
}

export function hasStableStatusState(ord: number): boolean {
  const stable = controlStateFor(ord).stableStatus;
  return stable.message !== "";
}

export function currentStatusState(ord: number): StoredEditorStatus {
  return controlStateFor(ord).currentStatus;
}

export function stableStatusState(ord: number): StoredEditorStatus {
  return controlStateFor(ord).stableStatus;
}

export function setHistorySnapshotState(ord: number, snapshot: HistorySnapshot, limit: number): HistorySnapshot {
  const normalized = {
    canRedo: !!snapshot.canRedo,
    canUndo: !!snapshot.canUndo,
    redoItems: snapshot.redoItems.slice(0, limit),
    undoItems: snapshot.undoItems.slice(0, limit),
  };
  controlStateFor(ord).historySnapshot = normalized;
  return normalized;
}

export function setHistoryAvailabilityState(ord: number, canUndo: boolean, canRedo: boolean): HistorySnapshot {
  return setHistorySnapshotState(ord, {
    canRedo: !!canRedo,
    canUndo: !!canUndo,
    redoItems: [],
    undoItems: [],
  }, 100);
}

export function historySnapshotState(ord: number): HistorySnapshot {
  return controlStateFor(ord).historySnapshot;
}

export function historyAvailabilityState(ord: number): { canRedo: boolean; canUndo: boolean } {
  const snapshot = historySnapshotState(ord);
  return { canRedo: snapshot.canRedo, canUndo: snapshot.canUndo };
}
