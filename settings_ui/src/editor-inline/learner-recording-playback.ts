import { t } from "../lib/i18n.js";
import { setStatusForOrd } from "./control-actions.js";
import {
  clearHtmlAudioSession,
  dispatchHtmlAudioSessionEvent,
  dispatchHtmlAudioSessionSourceFact,
  readHtmlAudioTransportSourceIdentity,
  readHtmlAudioTransportPosition,
  readHtmlAudioSessionState,
} from "./html-audio-session-controller.js";
import type { HtmlAudioStartRequest } from "./html-audio-session-machine.js";
import { logger } from "./logger.js";
import { syncRecordingControls } from "./recording-actions-sync.js";
import type { LearnerRecordingStatePayload } from "./recording-state.js";
import {
  readLearnerRecordingState,
  writeLearnerRecordingState,
} from "./recording-state-store.js";

export function toggleLearnerRecordingHtmlPlayback(ord: number): boolean {
  const session = readHtmlAudioSessionState(ord);
  if (session.kind === "playing" && session.source.kind === "learner_recording") {
    dispatchHtmlAudioSessionEvent(ord, {
      cursorMs: learnerAudioCurrentTimeMs(ord, session.durationMs),
      type: "PauseRequested",
    });
    logger.info("recording.playback.html_paused", { ord });
    return true;
  }
  if (session.kind === "paused" && session.source.kind === "learner_recording") {
    dispatchHtmlAudioSessionEvent(ord, { type: "ResumeRequested" });
    logger.info("recording.playback.html_resumed", { ord });
    return true;
  }
  const recording = readLearnerRecordingState(ord);
  if (!readyLearnerRecording(recording)) {
    setStatusForOrd(ord, t("editor.status.referenced_audio_missing"), "warning", "", "playback");
    logger.info("recording.playback.ignored_missing", { ord });
    return true;
  }
  configureLearnerSession(ord, recording);
  dispatchHtmlAudioSessionEvent(ord, {
    request: learnerStartRequest(ord, recording),
    type: "StartRequested",
  });
  logger.info("recording.playback.html_started", { ord });
  return true;
}

export function stopLearnerRecordingHtmlPlayback(ord: number): void {
  const session = readHtmlAudioSessionState(ord);
  if (session.kind === "empty" || session.kind === "failed" || session.source.kind !== "learner_recording") return;
  dispatchHtmlAudioSessionEvent(ord, { cursorMs: 0, type: "StopRequested" });
}

export function stopAllLearnerRecordingHtmlPlayback(): void {
  for (const ord of learnerSessionOrds()) {
    dispatchHtmlAudioSessionEvent(ord, { type: "RuntimeDisposed" });
  }
}

export function syncLearnerRecordingPlaybackState(
  ord: number,
  payload?: LearnerRecordingStatePayload,
): void {
  const recording = payload
    ? writeLearnerRecordingState(ord, payload)
    : readLearnerRecordingState(ord);
  if (!readyLearnerRecording(recording)) {
    const session = readHtmlAudioSessionState(ord);
    if (session.kind !== "empty" && session.kind !== "failed" && session.source.kind === "learner_recording") {
      clearHtmlAudioSession(ord);
    }
    syncRecordingControls(ord);
    return;
  }
  configureLearnerSession(ord, recording);
  syncRecordingControls(ord);
}

function configureLearnerSession(
  ord: number,
  recording: ReturnType<typeof readLearnerRecordingState>,
): void {
  const session = readHtmlAudioSessionState(ord);
  const source = {
    kind: "learner_recording" as const,
    attemptId: recording.attemptId ?? 0,
    sourceFilename: recording.mediaFilename,
    startCursorMs: recording.startCursorMs,
  };
  if (
    session.kind === "empty" ||
    session.kind === "failed" ||
    session.source.kind !== "learner_recording" ||
    session.source.sourceFilename !== source.sourceFilename ||
    session.source.attemptId !== source.attemptId
  ) {
    dispatchHtmlAudioSessionEvent(ord, {
      cursorMs: 0,
      source,
      type: "SourceConfigured",
    });
  }
  const current = readHtmlAudioSessionState(ord);
  if (current.kind === "loading") {
    const identity = readHtmlAudioTransportSourceIdentity(ord);
    if (!identity) return;
    dispatchHtmlAudioSessionSourceFact(ord, identity, {
      durationMs: learnerDurationMs(recording),
      type: "MetadataLoaded",
    });
  }
}

function learnerStartRequest(
  ord: number,
  recording: ReturnType<typeof readLearnerRecordingState>,
): HtmlAudioStartRequest {
  return {
    cursorMs: 0,
    endMs: learnerDurationMs(recording),
    loop: false,
    ord,
    regionMode: "full",
    resetCursorMs: 0,
    source: "learner_recording",
  };
}

function readyLearnerRecording(recording: ReturnType<typeof readLearnerRecordingState>): boolean {
  return recording.recordingStatus === "ready"
    && recording.mediaFilename.length > 0
    && recording.attemptId !== null;
}

function learnerDurationMs(recording: ReturnType<typeof readLearnerRecordingState>): number {
  return Math.max(0, recording.recordingDurationMs || recording.targetDurationMs || 0);
}

function learnerAudioCurrentTimeMs(ord: number, durationMs: number): number {
  const currentMs = readHtmlAudioTransportPosition(ord);
  return Math.max(0, Math.min(currentMs, Math.max(0, durationMs)));
}

function learnerSessionOrds(): number[] {
  const ords: number[] = [];
  document.querySelectorAll<HTMLElement>("[data-aqe-field-ord]").forEach((element) => {
    const ord = Number(element.dataset.aqeFieldOrd || "0");
    const session = readHtmlAudioSessionState(ord);
    if (session.kind !== "empty" && session.kind !== "failed" && session.source.kind === "learner_recording") {
      ords.push(ord);
    }
  });
  return Array.from(new Set(ords));
}
