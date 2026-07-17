import { startChorusingProgram } from "./chorusing.js";
import type {
  ChorusingProgramState,
  OnceProgramState,
  PracticeCommand,
  PracticeFact,
  PracticePlaybackPass,
  PracticeProgramState,
  PracticeRange,
  ProgramRunId,
  ProgramTransition,
  RecordingSpec,
  RecordOnceProgramState,
  RepeatProgramState,
} from "./model.js";
import { programIsTerminal } from "./model.js";
import { startOnceProgram } from "./once.js";
import { startRecordOnceProgram } from "./record-once.js";
import { reducePracticeProgram } from "./reducer.js";
import { startRepeatProgram } from "./repeat.js";

export interface PracticeScheduler {
  clear(handle: unknown): void;
  schedule(callback: () => void, durationMs: number): unknown;
}

export interface PracticeRuntimePorts {
  complete(runId: ProgramRunId): void;
  fail(runId: ProgramRunId, command: Extract<PracticeCommand, { type: "Fail" }>): void;
  requestPlay(runId: ProgramRunId, pass: PracticePlaybackPass): void;
  projectSelection(fieldOrd: number, range: PracticeRange): void;
  projectWait(
    fieldOrd: number,
    durationMs: number,
    waiting: boolean,
    purpose: "countdown" | "repeat_gap",
  ): void;
  startRecording(runId: ProgramRunId, spec: RecordingSpec): void;
  stopTransport(runId: ProgramRunId, fieldOrd: number): void;
}

export interface PracticeRuntimeSnapshot {
  readonly runId: ProgramRunId;
  readonly state: PracticeProgramState;
}

/** Owns one program run and every program wait/countdown handle. */
export class PracticeRuntime {
  private active: PracticeRuntimeSnapshot | null = null;
  private nextRunId = 1;
  private waitHandle: unknown = null;

  constructor(
    private readonly ports: PracticeRuntimePorts,
    private readonly scheduler: PracticeScheduler,
  ) {}

  readSnapshot(): PracticeRuntimeSnapshot | null {
    return this.active;
  }

  startOnce(pass: PracticePlaybackPass): ProgramRunId {
    return this.start(startOnceProgram(pass));
  }

  startRepeat(pass: PracticePlaybackPass, gapMs: number, count: number | null): ProgramRunId {
    return this.start(startRepeatProgram(pass, gapMs, count));
  }

  startChorusing(
    pass: PracticePlaybackPass,
    selection: PracticeRange,
    markersMs: readonly number[],
    repeatCount: number,
    gapMs: number,
  ): ProgramRunId {
    return this.start(startChorusingProgram(pass, selection, markersMs, repeatCount, gapMs));
  }

  startRecordOnce(countdownMs: number, spec: RecordingSpec): ProgramRunId {
    return this.start(startRecordOnceProgram(countdownMs, spec));
  }

  dispatch(runId: ProgramRunId, fact: PracticeFact): boolean {
    const current = this.active;
    if (!current || current.runId !== runId) return false;
    const transition = reducePracticeProgram(current.state, fact);
    this.apply(runId, transition);
    return true;
  }

  cancel(): void {
    const runId = this.active?.runId;
    if (runId !== undefined) this.dispatch(runId, { type: "Cancelled" });
    this.clearWait();
    this.active = null;
  }

  dispose(): void {
    this.cancel();
  }

  private start<State extends PracticeProgramState>(transition: ProgramTransition<State>): ProgramRunId {
    this.cancel();
    const runId = this.nextRunId++ as ProgramRunId;
    this.active = { runId, state: transition.state };
    this.execute(runId, transition.commands);
    if (programIsTerminal(transition.state)) this.active = null;
    return runId;
  }

  private apply(runId: ProgramRunId, transition: ProgramTransition<PracticeProgramState>): void {
    this.clearWait();
    this.active = { runId, state: transition.state };
    this.execute(runId, transition.commands);
    if (programIsTerminal(transition.state) && this.active?.runId === runId) this.active = null;
  }

  private execute(runId: ProgramRunId, commands: readonly PracticeCommand[]): void {
    for (const command of commands) {
      if (this.active?.runId !== runId) return;
      switch (command.type) {
        case "Play": this.ports.requestPlay(runId, command.pass); break;
        case "Wait": this.startWait(runId, command); break;
        case "UpdateSelectionProjection": this.ports.projectSelection(command.fieldOrd, command.range); break;
        case "StopTransport": this.ports.stopTransport(runId, command.fieldOrd); break;
        case "StartRecording": this.ports.startRecording(runId, command.spec); break;
        case "Complete": this.ports.complete(runId); break;
        case "Fail": this.ports.fail(runId, command); break;
        default: exhaustive(command);
      }
    }
  }

  private startWait(runId: ProgramRunId, command: Extract<PracticeCommand, { type: "Wait" }>): void {
    const fieldOrd = programFieldOrd(this.active!.state);
    let remainingMs = command.durationMs;
    const tick = (): void => {
      if (this.active?.runId !== runId) return;
      this.ports.projectWait(fieldOrd, remainingMs, true, command.purpose);
      const stepMs = Math.min(1000, remainingMs);
      this.waitHandle = this.scheduler.schedule(() => {
        this.waitHandle = null;
        if (this.active?.runId !== runId) return;
        remainingMs -= stepMs;
        if (remainingMs > 0) {
          tick();
          return;
        }
        this.ports.projectWait(fieldOrd, 0, false, command.purpose);
        this.dispatch(runId, { type: "WaitElapsed" });
      }, stepMs);
    };
    tick();
  }

  private clearWait(): void {
    if (this.waitHandle === null) return;
    this.scheduler.clear(this.waitHandle);
    const current = this.active;
    if (current) {
      const purpose = current.state.kind === "record_once" ? "countdown" : "repeat_gap";
      this.ports.projectWait(programFieldOrd(current.state), 0, false, purpose);
    }
    this.waitHandle = null;
  }
}

function programFieldOrd(state: PracticeProgramState): number {
  return state.kind === "record_once" ? state.spec.fieldOrd : state.pass.ord;
}

export const browserPracticeScheduler: PracticeScheduler = {
  clear: (handle) => window.clearTimeout(handle as number),
  schedule: (callback, durationMs) => window.setTimeout(callback, Math.max(0, durationMs)),
};

function exhaustive(value: never): never {
  throw new Error(`Unhandled practice command: ${JSON.stringify(value)}`);
}

export type ActivePlaybackProgramState = OnceProgramState | RepeatProgramState | ChorusingProgramState;
export type ActiveRecordingProgramState = RecordOnceProgramState;
