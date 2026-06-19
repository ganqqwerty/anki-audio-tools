import { t } from "../lib/i18n.js";
import { mediaUrlForFilename } from "./audio-clock.js";
import { setStatusForOrd } from "./control-actions.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { logger } from "./logger.js";
import {
  initialLearnerRecordingPlaybackState,
  transitionLearnerRecordingPlayback,
  type LearnerRecordingPlaybackEffect,
  type LearnerRecordingPlaybackEvent,
  type LearnerRecordingPlaybackState,
  type LearnerRecordingPlaybackTransition,
} from "./learner-recording-playback-machine.js";
import { setRecordingCursor } from "./recording-actions-state.js";
import { syncRecordingControls } from "./recording-actions-sync.js";
import type { LearnerRecordingStatePayload } from "./recording-state.js";
import {
  readLearnerRecordingState,
  writeLearnerRecordingState,
} from "./recording-state-store.js";

const playbackStates = new Map<number, LearnerRecordingPlaybackState>();
const audioByOrd = new Map<number, HTMLAudioElement>();
const frameByOrd = new Map<number, number>();
const pendingPlayModeByOrd = new Map<number, "started" | "resumed">();

export function toggleLearnerRecordingHtmlPlayback(ord: number): boolean {
  const current = ensurePlaybackState(ord);
  if (current.kind === "playing") {
    dispatchLearnerRecordingPlaybackEvent(ord, {
      cursorMs: learnerAudioCurrentTimeMs(audioByOrd.get(ord), current.durationMs),
      type: "PauseRequested",
    });
    return true;
  }
  if (current.kind === "paused") {
    dispatchLearnerRecordingPlaybackEvent(ord, { type: "ResumeRequested" });
    return true;
  }
  dispatchLearnerRecordingPlaybackEvent(ord, { type: "PlayButtonClicked" });
  return true;
}

export function stopLearnerRecordingHtmlPlayback(ord: number): void {
  dispatchLearnerRecordingPlaybackEvent(ord, { type: "StopRequested" });
}

export function stopAllLearnerRecordingHtmlPlayback(): void {
  for (const ord of knownLearnerPlaybackOrds()) {
    dispatchLearnerRecordingPlaybackEvent(ord, { type: "RuntimeDisposed" });
  }
  for (const [ord, audio] of audioByOrd) {
    removeLearnerAudio(ord, audio);
  }
  audioByOrd.clear();
  playbackStates.clear();
  pendingPlayModeByOrd.clear();
}

export function syncLearnerRecordingPlaybackState(
  ord: number,
  payload?: LearnerRecordingStatePayload,
): void {
  const state = readLearnerRecordingState(ord);
  dispatchLearnerRecordingPlaybackEvent(ord, {
    generation: payload?.generation ?? state.generation,
    mediaFilename: payload?.mediaFilename ?? state.mediaFilename,
    recordingDurationMs: payload?.recordingDurationMs ?? state.recordingDurationMs,
    startCursorMs: payload?.startCursorMs ?? state.startCursorMs,
    status: payload?.status ?? state.recordingStatus,
    targetDurationMs: payload?.targetDurationMs ?? state.targetDurationMs,
    type: "RecordingStatePublished",
  });
}

function ensurePlaybackState(ord: number): LearnerRecordingPlaybackState {
  if (!playbackStates.has(ord)) {
    syncLearnerRecordingPlaybackState(ord);
  }
  return playbackStates.get(ord) ?? initialLearnerRecordingPlaybackState();
}

function dispatchLearnerRecordingPlaybackEvent(
  ord: number,
  event: LearnerRecordingPlaybackEvent,
): void {
  const previous = playbackStates.get(ord) ?? initialLearnerRecordingPlaybackState();
  trackPendingPlayMode(ord, previous, event);
  const transition = transitionLearnerRecordingPlayback(previous, event);
  playbackStates.set(ord, transition.state);
  executeLearnerRecordingPlaybackTransition(ord, transition);
}

function executeLearnerRecordingPlaybackTransition(
  ord: number,
  transition: LearnerRecordingPlaybackTransition,
): void {
  for (const effect of transition.effects) {
    executeLearnerRecordingPlaybackEffect(ord, effect, transition.state);
  }
}

function executeLearnerRecordingPlaybackEffect(
  ord: number,
  effect: LearnerRecordingPlaybackEffect,
  state: LearnerRecordingPlaybackState,
): void {
  switch (effect.type) {
    case "ConfigureLearnerAudioSource":
      configureLearnerAudioSource(audioForOrd(ord), effect.mediaFilename);
      return;
    case "SeekLearnerAudio":
      seekLearnerAudio(audioForOrd(ord), effect.cursorMs);
      return;
    case "PlayLearnerAudio":
      playLearnerAudio(ord, audioForOrd(ord));
      return;
    case "PauseLearnerAudio":
      pauseLearnerAudio(ord, audioByOrd.get(ord), state);
      return;
    case "StopLearnerAudio":
      stopLearnerAudio(ord, audioByOrd.get(ord));
      return;
    case "StartLearnerProgressFrame":
      startLearnerProgressFrame(ord, state);
      return;
    case "ClearLearnerProgressFrame":
      clearLearnerProgressFrame(ord);
      return;
    case "PublishLearnerPlaybackState":
      publishLearnerPlaybackState(ord, effect);
      return;
    case "RenderLearnerPlaybackCursor":
      renderLearnerPlaybackCursor(ord, effect.cursorMs);
      return;
    case "ShowPlaybackStatus":
      setStatusForOrd(ord, t(effect.statusKey), effect.kind ?? "warning", "", "playback");
      return;
    case "LogPlaybackTelemetry":
      logger.info(effect.event, { ...effect.data, ord });
      return;
    default:
      return exhaustive(effect);
  }
}

function audioForOrd(ord: number): HTMLAudioElement {
  const existing = audioByOrd.get(ord);
  if (existing) return existing;
  const audio = document.createElement("audio");
  audio.dataset.testid = `aqe-learner-audio-${ord}`;
  audio.hidden = true;
  audio.preload = "auto";
  audio.addEventListener("ended", () => {
    logger.info("recording.playback.html_ended", { ord });
    dispatchLearnerRecordingPlaybackEvent(ord, { type: "AudioEnded" });
  });
  audio.addEventListener("error", () => {
    dispatchLearnerRecordingPlaybackEvent(ord, { reason: "audio_error", type: "AudioError" });
  });
  document.body.append(audio);
  audioByOrd.set(ord, audio);
  return audio;
}

function removeLearnerAudio(ord: number, audio: HTMLAudioElement): void {
  stopLearnerAudio(ord, audio);
  audio.remove();
}

function configureLearnerAudioSource(audio: HTMLAudioElement, mediaFilename: string): void {
  audio.setAttribute("src", mediaUrlForFilename(mediaFilename));
  try {
    audio.load();
  } catch {
    // Browser loading failures surface through the audio error/play rejection events.
  }
}

function seekLearnerAudio(audio: HTMLAudioElement, cursorMs: number): void {
  try {
    audio.currentTime = Math.max(0, Number(cursorMs) || 0) / 1000;
  } catch {
    // The reducer has no seek-failed learner event; playback rejection/error will stop the state.
  }
}

function playLearnerAudio(ord: number, audio: HTMLAudioElement): void {
  Promise.resolve(audio.play())
    .then(() => {
      const mode = pendingPlayModeByOrd.get(ord) ?? "started";
      pendingPlayModeByOrd.delete(ord);
      logger.info(
        mode === "resumed" ? "recording.playback.html_resumed" : "recording.playback.html_started",
        { ord },
      );
      dispatchLearnerRecordingPlaybackEvent(ord, {
        nowMs: performance.now(),
        type: "PlayResolved",
      });
    })
    .catch(() => {
      pendingPlayModeByOrd.delete(ord);
      dispatchLearnerRecordingPlaybackEvent(ord, {
        reason: "audio_play_rejected",
        type: "PlayRejected",
      });
    });
}

function pauseLearnerAudio(
  ord: number,
  audio: HTMLAudioElement | undefined,
  state: LearnerRecordingPlaybackState,
): void {
  if (audio) {
    try {
      audio.pause();
    } catch {
      // Pause failure should not leave the frontend state machine stuck.
    }
  }
  logger.info("recording.playback.html_paused", { ord });
  if (state.kind === "paused") {
    renderLearnerPlaybackCursor(ord, state.startCursorMs + state.cursorMs);
  }
}

function stopLearnerAudio(ord: number, audio: HTMLAudioElement | undefined): void {
  clearLearnerProgressFrame(ord);
  if (!audio) return;
  try {
    audio.pause();
  } catch {
    // Stop is best-effort during teardown.
  }
  try {
    audio.currentTime = 0;
  } catch {
    // Some media elements reject currentTime changes before metadata is available.
  }
}

function startLearnerProgressFrame(ord: number, state: LearnerRecordingPlaybackState): void {
  clearLearnerProgressFrame(ord);
  if (state.kind !== "playing") return;
  const tick = (): void => {
    const current = playbackStates.get(ord);
    if (!current || current.kind !== "playing") return;
    const audio = audioByOrd.get(ord);
    renderLearnerPlaybackCursor(
      ord,
      current.startCursorMs + learnerAudioCurrentTimeMs(audio, current.durationMs),
    );
    frameByOrd.set(ord, window.requestAnimationFrame(tick));
  };
  tick();
}

function clearLearnerProgressFrame(ord: number): void {
  const frame = frameByOrd.get(ord);
  if (frame !== undefined) {
    window.cancelAnimationFrame(frame);
  }
  frameByOrd.delete(ord);
}

function publishLearnerPlaybackState(
  ord: number,
  effect: Extract<LearnerRecordingPlaybackEffect, { type: "PublishLearnerPlaybackState" }>,
): void {
  const current = readLearnerRecordingState(ord);
  writeLearnerRecordingState(ord, {
    fieldOrd: ord,
    generation: current.generation,
    mediaFilename: current.mediaFilename,
    playbackStatus: effect.status,
    recordingDurationMs: current.recordingDurationMs,
    startCursorMs: current.startCursorMs,
    status: current.recordingStatus,
    targetDurationMs: current.targetDurationMs,
  });
  syncRecordingControls(ord);
}

function renderLearnerPlaybackCursor(ord: number, cursorMs: number): void {
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  const recording = readLearnerRecordingState(ord);
  const targetDurationMs = Math.max(
    recording.targetDurationMs,
    recording.startCursorMs + recording.recordingDurationMs,
    cursorMs,
  );
  setRecordingCursor(visualizer, cursorMs, targetDurationMs);
}

function trackPendingPlayMode(
  ord: number,
  previous: LearnerRecordingPlaybackState,
  event: LearnerRecordingPlaybackEvent,
): void {
  if (event.type === "ResumeRequested" || (event.type === "PlayButtonClicked" && previous.kind === "paused")) {
    pendingPlayModeByOrd.set(ord, "resumed");
    return;
  }
  if (event.type === "PlayButtonClicked" && previous.kind === "ready") {
    pendingPlayModeByOrd.set(ord, "started");
  }
}

function learnerAudioCurrentTimeMs(
  audio: HTMLAudioElement | undefined,
  durationMs: number,
): number {
  const currentMs = Math.round(Math.max(0, Number(audio?.currentTime) || 0) * 1000);
  return Math.max(0, Math.min(currentMs, Math.max(0, durationMs)));
}

function knownLearnerPlaybackOrds(): number[] {
  return Array.from(new Set([
    ...playbackStates.keys(),
    ...audioByOrd.keys(),
  ]));
}

function exhaustive(value: never): never {
  throw new Error(`Unhandled learner recording playback effect: ${JSON.stringify(value)}`);
}
