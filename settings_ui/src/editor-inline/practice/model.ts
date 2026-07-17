import type { PlaybackPass } from "../playback-model.js";
import type { TransportSourceIdentity } from "../transport/index.js";

export type ProgramRunId = number & { readonly __programRunId: unique symbol };

export interface PracticePlaybackPass extends PlaybackPass {
  readonly ord: number;
  readonly source: "learner_recording" | "post_edit" | "user";
}

export interface PracticeRange {
  readonly endMs: number;
  readonly startMs: number;
}

export interface RecordingSpec {
  readonly fieldOrd: number;
  readonly sourceIdentity: TransportSourceIdentity;
  readonly startCursorMs: number;
}

export type PracticeFailure =
  | { readonly kind: "invalid_markers" }
  | { readonly kind: "recorder_failed"; readonly message: string }
  | { readonly kind: "transport_failed"; readonly message: string };

export type PracticeCommand =
  | { readonly type: "Play"; readonly pass: PracticePlaybackPass }
  | { readonly type: "Wait"; readonly durationMs: number; readonly purpose: "countdown" | "repeat_gap" }
  | { readonly type: "UpdateSelectionProjection"; readonly fieldOrd: number; readonly range: PracticeRange }
  | { readonly type: "StopTransport"; readonly fieldOrd: number }
  | { readonly type: "StartRecording"; readonly spec: RecordingSpec }
  | { readonly type: "Complete" }
  | { readonly type: "Fail"; readonly reason: PracticeFailure };

export type PracticeFact =
  | { readonly type: "PassCompleted" }
  | { readonly type: "WaitElapsed" }
  | { readonly type: "RepeatDisabled" }
  | { readonly type: "PauseRequested" }
  | { readonly type: "ResumeRequested" }
  | { readonly type: "Stopped" }
  | { readonly type: "Cancelled" }
  | { readonly type: "SourceChanged" }
  | { readonly type: "SelectionChanged" }
  | { readonly type: "TransportStopped" }
  | { readonly type: "TransportResumed" }
  | { readonly type: "TransportFailed"; readonly message: string }
  | { readonly type: "MarkersUpdated"; readonly markersMs: readonly number[] }
  | { readonly type: "Skip" }
  | { readonly type: "RecorderStarted" }
  | { readonly type: "RecorderCompleted" }
  | { readonly type: "RecorderFailed"; readonly message: string };

export interface ProgramTransition<State> {
  readonly commands: readonly PracticeCommand[];
  readonly state: State;
}

export interface OnceProgramState {
  readonly kind: "once";
  readonly pass: PracticePlaybackPass;
  readonly phase: "cancelled" | "completed" | "failed" | "paused" | "playing";
}

export interface RepeatProgramState {
  readonly kind: "repeat";
  readonly completedPasses: number;
  readonly count: number | null;
  readonly finishAfterCurrentPass: boolean;
  readonly gapMs: number;
  readonly pass: PracticePlaybackPass;
  readonly phase: "cancelled" | "completed" | "failed" | "paused" | "playing" | "waiting";
}

export interface ChorusingProgramState {
  readonly kind: "chorusing";
  readonly completedPasses: number;
  readonly finishAfterCurrentPass: boolean;
  readonly gapMs: number;
  readonly markersMs: readonly number[];
  readonly pass: PracticePlaybackPass;
  readonly phase: "cancelled" | "completed" | "failed" | "paused" | "playing" | "waiting";
  readonly repeatCount: number;
  readonly selection: PracticeRange;
}

export interface RecordOnceProgramState {
  readonly countdownMs: number;
  readonly kind: "record_once";
  readonly phase:
    | "cancelled"
    | "completed"
    | "countdown"
    | "failed"
    | "recording"
    | "starting_recorder"
    | "stopping_transport";
  readonly spec: RecordingSpec;
}

export type PracticeProgramState =
  | OnceProgramState
  | RepeatProgramState
  | ChorusingProgramState
  | RecordOnceProgramState;

export function programIsTerminal(state: PracticeProgramState): boolean {
  return state.phase === "cancelled" || state.phase === "completed" || state.phase === "failed";
}
