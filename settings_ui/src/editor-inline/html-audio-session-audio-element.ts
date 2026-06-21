import { audioClockFor, mediaUrlForFilename, resetAudioClockState } from "./audio-clock.js";
import { markHtmlAudioFailure, publishAudioReadinessChange } from "./audio-readiness.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { installLearnerAudioHandlers } from "./html-audio-session-learner-projection.js";
import { logger } from "./logger.js";
import type { HtmlAudioSessionEvent, HtmlAudioSessionState } from "./html-audio-session-types.js";

type ReadHtmlAudioSessionState = (ord: number) => HtmlAudioSessionState;
type DispatchHtmlAudioSessionEvent = (ord: number, event: HtmlAudioSessionEvent) => void;

export interface HtmlAudioElementOperations {
  clearAudioSource: (ord: number) => void;
  configureAudioSource: (ord: number, sourceFilename: string) => void;
  pauseAudio: (ord: number) => void;
  playAudio: (ord: number) => void;
  reloadAudioSource: (ord: number) => void;
  seekAudio: (ord: number, cursorMs: number) => void;
}

export function createHtmlAudioElementOperations(
  readState: ReadHtmlAudioSessionState,
  dispatch: DispatchHtmlAudioSessionEvent,
): HtmlAudioElementOperations {
  return {
    clearAudioSource: (ord) => clearAudioSource(ord),
    configureAudioSource: (ord, sourceFilename) => configureAudioSource(ord, sourceFilename, readState, dispatch),
    pauseAudio: (ord) => pauseAudio(ord),
    playAudio: (ord) => playAudio(ord, readState, dispatch),
    reloadAudioSource: (ord) => reloadAudioSource(ord),
    seekAudio: (ord, cursorMs) => seekAudio(ord, cursorMs, dispatch),
  };
}

export function audioForOrd(ord: number): HTMLAudioElement | null {
  const visualizer = visualizerForOrd(ord);
  return document.querySelector<HTMLAudioElement>(`[data-testid="aqe-audio-clock-${ord}"]`) ?? audioClockFor(visualizer);
}

export function audioProgressMsForOrd(ord: number): number {
  const audio = audioForOrd(ord);
  return audio ? Math.round((Number(audio.currentTime) || 0) * 1000) : 0;
}

function configureAudioSource(
  ord: number,
  sourceFilename: string,
  readState: ReadHtmlAudioSessionState,
  dispatch: DispatchHtmlAudioSessionEvent,
): void {
  const visualizer = visualizerForOrd(ord);
  if (visualizer) resetAudioClockState(visualizer);
  const audio = audioForOrd(ord);
  if (!audio) {
    if (visualizer) {
      visualizer.__aqeAudioClockFallback = true;
      publishAudioReadinessChange(visualizer);
    }
    return;
  }
  installLearnerAudioHandlers(ord, audio, readState, dispatch);
  pauseAudio(ord);
  audio.loop = false;
  audio.setAttribute("src", mediaUrlForFilename(sourceFilename));
  logger.debug("html_audio_element.configure_source", {
    ord,
    readyState: audio.readyState,
    sourceFilename,
    src: audio.getAttribute("src") || "",
  });
  try {
    audio.load();
  } catch {
    if (visualizer) markHtmlAudioFailure(visualizer, "audio_load_failed");
    logger.debug("html audio session source load failed", { ord, sourceFilename });
  }
  if (visualizer) publishAudioReadinessChange(visualizer);
}

function seekAudio(ord: number, cursorMs: number, dispatch: DispatchHtmlAudioSessionEvent): void {
  const audio = audioForOrd(ord);
  if (!audio) return;
  try {
    audio.currentTime = Math.max(0, cursorMs) / 1000;
  } catch {
    dispatch(ord, {
      cursorMs,
      reason: "audio_seek_failed",
      type: "SeekFailed",
    });
  }
}

function reloadAudioSource(ord: number): void {
  const visualizer = visualizerForOrd(ord);
  const audio = audioForOrd(ord);
  if (!audio) return;
  audio.loop = false;
  try {
    audio.load();
  } catch {
    if (visualizer) markHtmlAudioFailure(visualizer, "audio_load_failed");
    logger.debug("html audio session source reload failed", { ord });
  }
  if (visualizer) publishAudioReadinessChange(visualizer);
}

function playAudio(
  ord: number,
  readState: ReadHtmlAudioSessionState,
  dispatch: DispatchHtmlAudioSessionEvent,
): void {
  const sourceFilename = sourceFilenameForCurrentSession(ord, readState);
  const audio = audioForOrd(ord);
  if (!audio) {
    dispatch(ord, { reason: "audio_play_rejected", sourceFilename, type: "PlayRejected" });
    return;
  }
  const state = readState(ord);
  if (state.kind !== "empty" && state.kind !== "failed" && state.source.kind === "learner_recording") {
    installLearnerAudioHandlers(ord, audio, readState, dispatch);
  }
  logger.debug("html_audio_element.play_requested", {
    currentTimeMs: Math.round((Number(audio.currentTime) || 0) * 1000),
    ord,
    readyState: audio.readyState,
    sourceFilename,
    src: audio.getAttribute("src") || "",
    stateKind: state.kind,
  });
  Promise.resolve(audio.play())
    .then(() => {
      logger.debug("html_audio_element.play_resolved", {
        currentTimeMs: Math.round((Number(audio.currentTime) || 0) * 1000),
        ord,
        readyState: audio.readyState,
        sourceFilename,
        src: audio.getAttribute("src") || "",
      });
      dispatch(ord, { nowMs: Date.now(), sourceFilename, type: "PlayResolved" });
    })
    .catch(() => {
      logger.debug("html_audio_element.play_rejected", {
        currentTimeMs: Math.round((Number(audio.currentTime) || 0) * 1000),
        ord,
        readyState: audio.readyState,
        sourceFilename,
        src: audio.getAttribute("src") || "",
      });
      dispatch(ord, { reason: "audio_play_rejected", sourceFilename, type: "PlayRejected" });
    });
}

function pauseAudio(ord: number): void {
  const visualizer = visualizerForOrd(ord);
  const audio = audioForOrd(ord);
  if (!audio) return;
  try {
    audio.pause();
  } catch {
    if (visualizer) markHtmlAudioFailure(visualizer, "audio_pause_failed");
    logger.debug("html audio session pause failed", { ord });
  }
}

function clearAudioSource(ord: number): void {
  const visualizer = visualizerForOrd(ord);
  if (visualizer) resetAudioClockState(visualizer);
  const audio = audioForOrd(ord);
  if (!audio) return;
  try {
    audio.pause();
  } catch {
    if (visualizer) markHtmlAudioFailure(visualizer, "audio_pause_failed");
    logger.debug("html audio session pause during clear failed", { ord });
  }
  audio.src = "";
  audio.removeAttribute("src");
  try {
    audio.load();
  } catch {
    if (visualizer) markHtmlAudioFailure(visualizer, "audio_load_failed");
    logger.debug("html audio session source clear load failed", { ord });
  }
  if (visualizer) publishAudioReadinessChange(visualizer);
}

function sourceFilenameForCurrentSession(ord: number, readState: ReadHtmlAudioSessionState): string {
  const state = readState(ord);
  return state.kind === "empty" || state.kind === "failed" ? "" : state.source.sourceFilename;
}
