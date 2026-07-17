import type { RecorderSnapshot } from "../lib/generated/contracts.js";
import { chorusingStateForVisualizer } from "./chorusing-dom.js";
import { visualizerForOrd } from "./dom-selectors.js";
import {
  dispatchHtmlAudioSessionEvent,
  readHtmlAudioSessionState,
  setHtmlAudioTransportFailureSink,
  setHtmlAudioTransportPassCompletedSink,
  stopAndQuiesceHtmlAudioTransport,
} from "./html-audio-session-controller.js";
import {
  completePlayback,
  publishPlaybackState,
} from "./html-audio-session-field-projection.js";
import type { HtmlAudioStartRequest } from "./html-audio-session-types.js";
import { logger } from "./logger.js";
import {
  bindPracticeRecordingRun,
  clearPracticeRecording,
  preparePracticeRecording,
  readPracticeRecordingProjection,
  receivePracticeRecorderSnapshot,
  startPracticeRecording,
} from "./editor-practice-recording.js";
import {
  projectPracticeChorusingState,
  projectPracticeSelection,
  projectPracticeWait,
} from "./editor-practice-projections.js";
import type {
  PracticeFailure,
  PracticePlaybackPass,
  ProgramRunId,
} from "./practice/index.js";
import {
  browserPracticeScheduler,
  PracticeRuntime,
  type PracticeRuntimeSnapshot,
} from "./practice/index.js";
import { selectionForVisualizer } from "./selection-controller.js";
import { getSplitButtonState } from "./split-button-state.js";
import { readRepeatPauseSecondsRuntime } from "./visualizer-runtime-state.js";

const practiceRuntime = new PracticeRuntime({
  complete: (runId) => clearPracticeRecording(runId),
  fail: (runId, command) => {
    clearPracticeRecording(runId);
    logPracticeFailure(runId, command.reason);
  },
  requestPlay: (_runId, pass) => dispatchHtmlAudioSessionEvent(pass.ord, {
    request: requestForPass(pass),
    type: "StartRequested",
  }),
  projectSelection: projectPracticeSelection,
  projectWait,
  startRecording: (runId, spec) => startPracticeRecording(
    runId,
    spec,
    (activeRunId, fact) => practiceRuntime.dispatch(activeRunId, fact),
  ),
  stopTransport: (runId, fieldOrd) => {
    stopAndQuiesceHtmlAudioTransport();
    practiceRuntime.dispatch(runId, { type: "TransportStopped" });
    logger.debug("practice.transport_quiesced", { fieldOrd, runId });
  },
}, browserPracticeScheduler);

export function initializeEditorPracticeRuntime(): void {
  practiceRuntime.dispose();
  clearPracticeRecording();
  setHtmlAudioTransportFailureSink(receiveEditorTransportFailure);
  setHtmlAudioTransportPassCompletedSink(handleTransportPassCompleted);
}

export function disposeEditorPracticeRuntime(): void {
  practiceRuntime.dispose();
  clearPracticeRecording();
  setHtmlAudioTransportFailureSink(null);
  setHtmlAudioTransportPassCompletedSink(null);
}

export function readEditorPracticeSnapshot(): PracticeRuntimeSnapshot | null {
  return practiceRuntime.readSnapshot();
}

function receiveEditorTransportFailure(fact: { readonly fieldOrd: number; readonly reason: string }): boolean {
  const snapshot = practiceRuntime.readSnapshot();
  if (!snapshot || programFieldOrd(snapshot) !== fact.fieldOrd) return false;
  return practiceRuntime.dispatch(snapshot.runId, {
    message: fact.reason,
    type: "TransportFailed",
  });
}

export function receiveEditorRecorderSnapshot(payload: RecorderSnapshot): boolean {
  return receivePracticeRecorderSnapshot(
    payload,
    practiceRuntime.readSnapshot(),
    (runId, fact) => practiceRuntime.dispatch(runId, fact),
  );
}

export function editorPracticePlaybackState(fieldOrd: number): "paused" | "playing" | "stopped" {
  const snapshot = practiceRuntime.readSnapshot();
  if (!snapshot || programFieldOrd(snapshot) !== fieldOrd || snapshot.state.kind === "record_once") return "stopped";
  if (snapshot.state.phase === "paused") return "paused";
  return snapshot.state.phase === "playing" || snapshot.state.phase === "waiting" ? "playing" : "stopped";
}

export function startEditorPlaybackPractice(
  visualizer: HTMLElement,
  request: HtmlAudioStartRequest,
): ProgramRunId {
  const pass = passForRequest(request);
  const split = getSplitButtonState(request.ord);
  const selection = selectionForVisualizer(visualizer);
  const gapMs = Math.max(0, readRepeatPauseSecondsRuntime(visualizer) * 1000);
  if (
    request.loop
    && request.regionMode === "selection"
    && split.chorusingAutoAdvance
    && selection
  ) {
    const chorusing = chorusingStateForVisualizer(visualizer);
    return practiceRuntime.startChorusing(
      pass,
      selection,
      chorusing.markersMs,
      split.chorusingRepeatCount,
      gapMs,
    );
  }
  if (request.loop) return practiceRuntime.startRepeat(pass, gapMs, null);
  return practiceRuntime.startOnce(pass);
}

export function startEditorRecordOnce(
  node: HTMLElement,
  fieldOrd: number,
  countdownMs: number,
  startCursorMs: number,
  targetDurationMs: number,
): boolean {
  const spec = preparePracticeRecording(node, fieldOrd, startCursorMs, targetDurationMs);
  if (!spec) return false;
  bindPracticeRecordingRun(practiceRuntime.startRecordOnce(countdownMs, spec));
  return true;
}

export function cancelEditorPracticeProgram(fieldOrd?: number): void {
  const snapshot = practiceRuntime.readSnapshot();
  if (!snapshot) return;
  if (fieldOrd !== undefined && programFieldOrd(snapshot) !== fieldOrd) return;
  practiceRuntime.cancel();
  clearPracticeRecording(snapshot.runId);
}

export function stopEditorPracticeProgram(fieldOrd: number): void {
  const snapshot = practiceRuntime.readSnapshot();
  if (!snapshot || programFieldOrd(snapshot) !== fieldOrd) return;
  practiceRuntime.dispatch(snapshot.runId, { type: "Stopped" });
}

export function pauseEditorPracticeWait(fieldOrd: number): boolean {
  const snapshot = practiceRuntime.readSnapshot();
  if (
    !snapshot
    || programFieldOrd(snapshot) !== fieldOrd
    || snapshot.state.kind === "record_once"
    || snapshot.state.phase !== "waiting"
  ) return false;
  if (!practiceRuntime.dispatch(snapshot.runId, { type: "PauseRequested" })) return false;
  const session = readHtmlAudioSessionState(fieldOrd);
  publishPlaybackState({
    cursorMs: snapshot.state.pass.resetCursorMs,
    ord: fieldOrd,
    request: requestForPass(snapshot.state.pass),
    session,
    status: "paused",
  });
  return true;
}

export function pauseEditorPracticeProgram(fieldOrd: number): boolean {
  const snapshot = practiceRuntime.readSnapshot();
  if (
    !snapshot
    || programFieldOrd(snapshot) !== fieldOrd
    || snapshot.state.kind === "record_once"
    || snapshot.state.phase !== "playing"
  ) return false;
  return practiceRuntime.dispatch(snapshot.runId, { type: "PauseRequested" });
}

export function resumeEditorPracticeProgram(fieldOrd: number, transportWillResume: boolean): boolean {
  const snapshot = practiceRuntime.readSnapshot();
  if (
    !snapshot
    || programFieldOrd(snapshot) !== fieldOrd
    || snapshot.state.kind === "record_once"
    || snapshot.state.phase !== "paused"
  ) return false;
  return practiceRuntime.dispatch(snapshot.runId, {
    type: transportWillResume ? "TransportResumed" : "ResumeRequested",
  });
}

export function disableEditorPracticeRepeat(fieldOrd: number): boolean {
  const snapshot = practiceRuntime.readSnapshot();
  if (
    !snapshot
    || programFieldOrd(snapshot) !== fieldOrd
    || (snapshot.state.kind !== "repeat" && snapshot.state.kind !== "chorusing")
  ) return false;
  const wasWaiting = snapshot.state.phase === "waiting";
  const cursorMs = snapshot.state.pass.resetCursorMs;
  practiceRuntime.dispatch(snapshot.runId, { type: "RepeatDisabled" });
  if (wasWaiting) completePlayback(fieldOrd, cursorMs);
  return true;
}

function handleTransportPassCompleted(ord: number, request: HtmlAudioStartRequest): boolean {
  const snapshot = practiceRuntime.readSnapshot();
  if (!snapshot || programFieldOrd(snapshot) !== ord || snapshot.state.kind === "record_once") return false;
  if (snapshot.state.kind === "chorusing") {
    const visualizer = visualizerForOrd(ord);
    if (visualizer) {
      practiceRuntime.dispatch(snapshot.runId, {
        markersMs: chorusingStateForVisualizer(visualizer).markersMs,
        type: "MarkersUpdated",
      });
    }
  }
  const current = practiceRuntime.readSnapshot();
  if (!current || current.runId !== snapshot.runId || current.state.kind === "record_once") return false;
  if (current.state.pass.endMs !== request.endMs || current.state.pass.regionMode !== request.regionMode) return false;
  practiceRuntime.dispatch(current.runId, { type: "PassCompleted" });
  projectPracticeChorusingState(ord, practiceRuntime.readSnapshot());
  return practiceRuntime.readSnapshot()?.runId === current.runId;
}

function passForRequest(request: HtmlAudioStartRequest): PracticePlaybackPass {
  return {
    endMs: request.endMs,
    loop: false,
    ord: request.ord,
    regionMode: request.regionMode,
    resetCursorMs: request.resetCursorMs ?? request.cursorMs,
    source: request.source,
    startMs: request.cursorMs,
  };
}

function requestForPass(pass: PracticePlaybackPass): HtmlAudioStartRequest {
  return {
    cursorMs: pass.startMs,
    endMs: pass.endMs,
    loop: false,
    ord: pass.ord,
    regionMode: pass.regionMode,
    resetCursorMs: pass.resetCursorMs,
    source: pass.source,
  };
}

function projectWait(
  fieldOrd: number,
  durationMs: number,
  waiting: boolean,
  purpose: "countdown" | "repeat_gap",
): void {
  projectPracticeWait(
    fieldOrd,
    durationMs,
    waiting,
    purpose,
    readPracticeRecordingProjection(),
    readPracticeResetCursorMs(fieldOrd),
  );
}

function readPracticeResetCursorMs(fieldOrd: number): number {
  const snapshot = practiceRuntime.readSnapshot();
  if (!snapshot || programFieldOrd(snapshot) !== fieldOrd || snapshot.state.kind === "record_once") return 0;
  return snapshot.state.pass.resetCursorMs;
}

function programFieldOrd(snapshot: PracticeRuntimeSnapshot): number {
  return snapshot.state.kind === "record_once" ? snapshot.state.spec.fieldOrd : snapshot.state.pass.ord;
}

function logPracticeFailure(runId: ProgramRunId, reason: PracticeFailure): void {
  if (reason.kind === "transport_failed") {
    logger.warn("practice.program_failed", { reason, runId });
    return;
  }
  logger.error("practice.program_failed", { reason, runId });
}
