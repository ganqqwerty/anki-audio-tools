import type { HtmlAudioSessionState } from "../html-audio-session-types.js";

export interface TransportViolation {
  readonly invariantId: "T-01" | "T-02" | "T-04";
  readonly message: string;
}

export interface TransportResourceSnapshot {
  readonly hasMetadataTimer: boolean;
  readonly hasProgressFrame: boolean;
}

export function validateTransportState(state: HtmlAudioSessionState): readonly TransportViolation[] {
  if (state.ord < 0 || !Number.isInteger(state.ord)) {
    return [{ invariantId: "T-02", message: "transport field ordinal is invalid" }];
  }
  if ((state.kind === "ready" || state.kind === "starting" || state.kind === "playing" || state.kind === "paused")
    && state.durationMs <= 0) {
    return [{ invariantId: "T-02", message: `${state.kind} transport has no media duration` }];
  }
  if ((state.kind === "starting" || state.kind === "playing" || state.kind === "paused")
    && (state.request.cursorMs < 0 || state.request.endMs <= state.request.cursorMs)) {
    return [{ invariantId: "T-02", message: `${state.kind} transport has invalid pass coordinates` }];
  }
  return [];
}

export function validateTransportOwnership(
  states: ReadonlyMap<number, HtmlAudioSessionState>,
): readonly TransportViolation[] {
  const active = [...states.values()].filter((state) => (
    state.kind === "starting" || state.kind === "playing" || state.kind === "paused"
  ));
  return active.length <= 1
    ? []
    : [{ invariantId: "T-01", message: "multiple fields own active transport state" }];
}

export function validateTransportResources(
  state: HtmlAudioSessionState,
  resources: TransportResourceSnapshot,
): readonly TransportViolation[] {
  const allowsProgress = state.kind === "starting" || state.kind === "playing";
  const allowsMetadata = state.kind === "loading";
  return [
    ...(!allowsProgress && resources.hasProgressFrame
      ? [{ invariantId: "T-04" as const, message: "terminal transport retains progress frame" }]
      : []),
    ...(!allowsMetadata && resources.hasMetadataTimer
      ? [{ invariantId: "T-04" as const, message: "terminal transport retains metadata timer" }]
      : []),
  ];
}
