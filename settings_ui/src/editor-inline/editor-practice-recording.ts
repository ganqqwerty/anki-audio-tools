import {
  RecorderCommandKind,
  Status,
  type RecorderCommand,
  type RecorderSnapshot,
} from "../lib/generated/contracts.js";
import { sendBridgeEnvelope } from "../lib/bridge-transport.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { graphSettingsForField } from "./graph-split-state.js";
import { clearGraphCountdownOverlay } from "./graph-countdown-overlay.js";
import { readHtmlAudioTransportSourceIdentity } from "./html-audio-session-controller.js";
import { logger } from "./logger.js";
import type { PracticeRecordingProjection } from "./editor-practice-projections.js";
import type {
  PracticeFact,
  PracticeRuntimeSnapshot,
  ProgramRunId,
  RecordingSpec,
} from "./practice/index.js";
import { recordingTargetReady } from "./recording-actions-state.js";

interface RecordingContext {
  attemptId: number | null;
  readonly node: HTMLElement;
  runId: ProgramRunId | null;
  readonly spec: RecordingSpec;
  readonly targetDurationMs: number;
}

type DispatchPracticeFact = (runId: ProgramRunId, fact: PracticeFact) => boolean;

let recordingContext: RecordingContext | null = null;

export function preparePracticeRecording(
  node: HTMLElement,
  fieldOrd: number,
  startCursorMs: number,
  targetDurationMs: number,
): RecordingSpec | null {
  const sourceIdentity = readHtmlAudioTransportSourceIdentity(fieldOrd);
  if (!sourceIdentity) return null;
  const spec = { fieldOrd, sourceIdentity, startCursorMs };
  recordingContext = {
    attemptId: null,
    node,
    runId: null,
    spec,
    targetDurationMs,
  };
  return spec;
}

export function bindPracticeRecordingRun(runId: ProgramRunId): void {
  if (recordingContext) recordingContext.runId = runId;
}

export function clearPracticeRecording(runId?: ProgramRunId): void {
  if (runId === undefined || recordingContext?.runId === runId) recordingContext = null;
}

export function readPracticeRecordingProjection(): PracticeRecordingProjection | null {
  const context = recordingContext;
  return context && {
    fieldOrd: context.spec.fieldOrd,
    startCursorMs: context.spec.startCursorMs,
    targetDurationMs: context.targetDurationMs,
  };
}

export function receivePracticeRecorderSnapshot(
  payload: RecorderSnapshot,
  snapshot: PracticeRuntimeSnapshot | null,
  dispatch: DispatchPracticeFact,
): boolean {
  const context = recordingContext;
  if (
    !snapshot
    || snapshot.state.kind !== "record_once"
    || !context
    || context.spec !== snapshot.state.spec
    || payload.fieldOrd !== context.spec.fieldOrd
    || payload.attemptId === null
  ) return false;
  if (context.attemptId === null) {
    if (payload.status !== Status.Starting && payload.status !== Status.Recording) return false;
    context.attemptId = payload.attemptId;
  } else if (context.attemptId !== payload.attemptId) {
    logger.debug("practice.stale_recorder_snapshot_ignored", {
      activeAttemptId: context.attemptId,
      fieldOrd: payload.fieldOrd,
      receivedAttemptId: payload.attemptId,
      runId: snapshot.runId,
    });
    return false;
  }
  if (payload.status === Status.Recording) {
    return dispatch(snapshot.runId, { type: "RecorderStarted" });
  }
  if (payload.status === Status.Analyzing || payload.status === Status.Ready) {
    return dispatch(snapshot.runId, { type: "RecorderCompleted" });
  }
  if (payload.status === Status.Failed) {
    return dispatch(snapshot.runId, {
      message: payload.failureMessage || "Recorder failed.",
      type: "RecorderFailed",
    });
  }
  return false;
}

export function startPracticeRecording(
  runId: ProgramRunId,
  spec: RecordingSpec,
  dispatch: DispatchPracticeFact,
): void {
  const context = recordingContext;
  const currentSource = readHtmlAudioTransportSourceIdentity(spec.fieldOrd);
  if (
    !context
    || context.spec !== spec
    || !currentSource
    || currentSource.runtimeId !== spec.sourceIdentity.runtimeId
    || currentSource.fieldInstanceId !== spec.sourceIdentity.fieldInstanceId
    || currentSource.sourceInstanceId !== spec.sourceIdentity.sourceInstanceId
    || !recordingTargetReady(spec.fieldOrd)
  ) {
    dispatch(runId, { type: "SourceChanged" });
    return;
  }
  const visualizer = visualizerForOrd(spec.fieldOrd);
  if (visualizer) clearGraphCountdownOverlay(visualizer);
  context.node.focus?.();
  window.__aqeActiveField = spec.fieldOrd;
  const command: RecorderCommand = {
    fieldOrd: spec.fieldOrd,
    graphSettings: graphSettingsForField(spec.fieldOrd),
    kind: RecorderCommandKind.Start,
    schemaVersion: 1,
    startCursorMs: spec.startCursorMs,
  };
  sendBridgeEnvelope("editor.recorder-command", command);
}
