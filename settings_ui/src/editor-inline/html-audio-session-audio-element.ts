import { visualizerForOrd } from "./dom-selectors.js";
import { logger } from "./logger.js";
import type {
  TransportAttemptIdentity,
  TransportSourceIdentity,
} from "./transport/index.js";

interface AudioRegistration {
  readonly audio: HTMLAudioElement;
  attemptIdentity: TransportAttemptIdentity | null;
  readonly sourceIdentity: TransportSourceIdentity;
}

interface InstalledAudioHandlers {
  readonly audio: HTMLAudioElement;
  readonly ended: () => void;
  readonly error: () => void;
  readonly loadedmetadata: () => void;
}

export interface HtmlAudioPortCallbacks {
  currentAttemptIdentity: (ord: number) => TransportAttemptIdentity | null;
  onAudioError: (
    ord: number,
    identity: TransportSourceIdentity | TransportAttemptIdentity,
    cursorMs: number,
    mediaErrorCode: number | null,
    mediaResponseStatus: number | null,
  ) => void;
  onEnded: (ord: number, identity: TransportAttemptIdentity, cursorMs: number) => void;
  onMetadataLoaded: (ord: number, identity: TransportSourceIdentity, durationMs: number) => void;
  onPlayRejected: (ord: number, identity: TransportAttemptIdentity) => void;
  onPlayResolved: (ord: number, identity: TransportAttemptIdentity, nowMs: number) => void;
  onSeekFailed: (ord: number, identity: TransportAttemptIdentity, cursorMs: number) => void;
}

export interface HtmlAudioElementOperations {
  clearAudioSource: (ord: number) => void;
  configureAudioSource: (
    ord: number,
    sourceFilename: string,
    identity: TransportSourceIdentity,
  ) => void;
  dispose: (ord: number) => void;
  pauseAudio: (ord: number) => void;
  playAudio: (ord: number, identity: TransportAttemptIdentity) => void;
  previewPosition: (ord: number, cursorMs: number, durationMs: number) => boolean;
  readSnapshot: (ord: number) => HtmlAudioPortSnapshot;
  reloadAudioSource: (ord: number, identity: TransportAttemptIdentity) => void;
  seekAudio: (ord: number, cursorMs: number, identity: TransportAttemptIdentity) => void;
}

export interface HtmlAudioPortSnapshot {
  currentTimeMs: number;
  hasSource: boolean;
  paused: boolean;
  present: boolean;
  readyState: number | null;
  sourceUrl: string;
}

const registrations = new Map<number, AudioRegistration>();
const installedHandlers = new Map<number, InstalledAudioHandlers>();

export function createHtmlAudioElementOperations(
  callbacks: HtmlAudioPortCallbacks,
): HtmlAudioElementOperations {
  return {
    clearAudioSource,
    configureAudioSource: (ord, sourceFilename, identity) => configureAudioSource(
      ord,
      sourceFilename,
      identity,
      callbacks,
    ),
    dispose: (ord) => disposeAudioPort(ord),
    pauseAudio: (ord) => pauseAudio(ord, callbacks),
    playAudio: (ord, identity) => playAudio(ord, identity, callbacks),
    previewPosition,
    readSnapshot: audioPortSnapshot,
    reloadAudioSource: (ord, identity) => reloadAudioSource(ord, identity),
    seekAudio: (ord, cursorMs, identity) => seekAudio(ord, cursorMs, identity, callbacks),
  };
}

function audioForOrd(ord: number): HTMLAudioElement | null {
  const visualizer = visualizerForOrd(ord);
  return document.querySelector<HTMLAudioElement>(`[data-testid="aqe-audio-clock-${ord}"]`)
    ?? visualizer?.querySelector<HTMLAudioElement>(".aqe-audio-clock")
    ?? null;
}

export function audioProgressMsForOrd(ord: number): number {
  const audio = audioForOrd(ord);
  return audio ? audioCurrentTimeMs(audio) : 0;
}

function configureAudioSource(
  ord: number,
  sourceFilename: string,
  identity: TransportSourceIdentity,
  callbacks: HtmlAudioPortCallbacks,
): void {
  const audio = audioForOrd(ord);
  if (!audio) return;
  installStableAudioHandlers(ord, audio, callbacks);
  registrations.set(ord, { audio, attemptIdentity: null, sourceIdentity: identity });
  pauseAudio(ord, callbacks, false);
  audio.loop = false;
  audio.setAttribute("src", mediaUrlForFilename(sourceFilename));
  logger.debug("html_audio_port.configure_source", {
    fieldInstanceId: identity.fieldInstanceId,
    ord,
    readyState: audio.readyState,
    runtimeId: identity.runtimeId,
    sourceFilename,
    sourceInstanceId: identity.sourceInstanceId,
    src: audio.getAttribute("src") || "",
  });
  try {
    audio.load();
  } catch {
    callbacks.onAudioError(ord, identity, 0, audio.error?.code ?? null, null);
  }
}

function seekAudio(
  ord: number,
  cursorMs: number,
  identity: TransportAttemptIdentity,
  callbacks: HtmlAudioPortCallbacks,
): void {
  const audio = audioForOrd(ord);
  if (!audio) return;
  ensureAttemptRegistration(ord, audio, identity, callbacks);
  try {
    audio.currentTime = Math.max(0, cursorMs) / 1000;
  } catch {
    callbacks.onSeekFailed(ord, identity, cursorMs);
  }
}

function reloadAudioSource(ord: number, identity: TransportAttemptIdentity): void {
  const audio = audioForOrd(ord);
  if (!audio) return;
  const registration = registrations.get(ord);
  if (registration) registration.attemptIdentity = identity;
  audio.loop = false;
  try {
    audio.load();
  } catch {
    logger.debug("html audio session source reload failed", { ord });
  }
}

function playAudio(
  ord: number,
  identity: TransportAttemptIdentity,
  callbacks: HtmlAudioPortCallbacks,
): void {
  const audio = audioForOrd(ord);
  if (!audio) {
    callbacks.onPlayRejected(ord, identity);
    return;
  }
  ensureAttemptRegistration(ord, audio, identity, callbacks);
  logger.debug("html_audio_port.play_requested", {
    attemptId: identity.attemptId,
    currentTimeMs: audioCurrentTimeMs(audio),
    fieldInstanceId: identity.fieldInstanceId,
    ord,
    readyState: audio.readyState,
    runtimeId: identity.runtimeId,
    sourceInstanceId: identity.sourceInstanceId,
    src: audio.getAttribute("src") || "",
  });
  Promise.resolve(audio.play())
    .then(() => callbacks.onPlayResolved(ord, identity, Date.now()))
    .catch(() => callbacks.onPlayRejected(ord, identity));
}

function ensureAttemptRegistration(
  ord: number,
  audio: HTMLAudioElement,
  identity: TransportAttemptIdentity,
  callbacks: HtmlAudioPortCallbacks,
): void {
  const registration = registrations.get(ord);
  if (!registration || registration.audio !== audio) {
    installStableAudioHandlers(ord, audio, callbacks);
    registrations.set(ord, {
      attemptIdentity: identity,
      audio,
      sourceIdentity: identity,
    });
    return;
  }
  registration.attemptIdentity = identity;
}

function pauseAudio(ord: number, callbacks: HtmlAudioPortCallbacks, reportFailure = true): void {
  const audio = audioForOrd(ord);
  if (!audio) return;
  try {
    audio.pause();
  } catch {
    logger.debug("html audio session pause failed", { ord });
    const registration = currentRegistration(ord, audio);
    if (reportFailure && registration) {
      callbacks.onAudioError(
        ord,
        registration.sourceIdentity,
        audioCurrentTimeMs(audio),
        audio.error?.code ?? null,
        null,
      );
    }
  }
}

function clearAudioSource(ord: number): void {
  const audio = audioForOrd(ord);
  registrations.delete(ord);
  if (!audio) return;
  try {
    audio.pause();
  } catch {
    logger.debug("html audio session pause during clear failed", { ord });
  }
  audio.src = "";
  audio.removeAttribute("src");
  try {
    audio.load();
  } catch {
    logger.debug("html audio session source clear load failed", { ord });
  }
}

function installStableAudioHandlers(
  ord: number,
  audio: HTMLAudioElement,
  callbacks: HtmlAudioPortCallbacks,
): void {
  const existing = installedHandlers.get(ord);
  if (existing?.audio === audio) return;
  if (existing) removeInstalledHandlers(existing);

  const loadedmetadata = (): void => {
    const registration = currentRegistration(ord, audio);
    if (!registration || !audio.getAttribute("src")) return;
    const durationMs = audioDurationMs(audio);
    if (durationMs <= 0) return;
    callbacks.onMetadataLoaded(ord, registration.sourceIdentity, durationMs);
  };
  const ended = (): void => {
    const registration = currentRegistration(ord, audio);
    const attemptIdentity = callbacks.currentAttemptIdentity(ord);
    if (!registration || !attemptIdentity) return;
    callbacks.onEnded(ord, attemptIdentity, audioBoundaryDurationMs(audio));
  };
  const error = (): void => {
    const registration = currentRegistration(ord, audio);
    if (!registration) return;
    const identity = registration.attemptIdentity ?? registration.sourceIdentity;
    const mediaErrorCode = audio.error?.code ?? null;
    const failedSrc = audio.getAttribute("src") || "";
    const report = (mediaResponseStatus: number | null): void => {
      if (audio.getAttribute("src") !== failedSrc) return;
      callbacks.onAudioError(ord, identity, audioCurrentTimeMs(audio), mediaErrorCode, mediaResponseStatus);
    };
    if (mediaErrorCode === 3 || mediaErrorCode === 4) {
      void mediaResponseStatusFor(failedSrc).then(report);
    } else {
      report(null);
    }
  };
  const handlers = { audio, ended, error, loadedmetadata };
  audio.addEventListener("loadedmetadata", loadedmetadata);
  audio.addEventListener("ended", ended);
  audio.addEventListener("error", error);
  installedHandlers.set(ord, handlers);
}

function disposeAudioPort(ord: number): void {
  registrations.delete(ord);
  const handlers = installedHandlers.get(ord);
  if (handlers) {
    removeInstalledHandlers(handlers);
    installedHandlers.delete(ord);
  }
}

function previewPosition(ord: number, cursorMs: number, durationMs: number): boolean {
  const audio = audioForOrd(ord);
  if (!audio) return false;
  const clamped = Math.max(0, Math.min(Number(cursorMs) || 0, durationMs || 0));
  try {
    audio.currentTime = clamped / 1000;
    return true;
  } catch {
    return false;
  }
}

function audioPortSnapshot(ord: number): HtmlAudioPortSnapshot {
  const audio = audioForOrd(ord);
  return {
    currentTimeMs: audio ? audioCurrentTimeMs(audio) : 0,
    hasSource: !!audio?.getAttribute("src"),
    paused: audio?.paused ?? true,
    present: audio !== null,
    readyState: typeof audio?.readyState === "number" ? audio.readyState : null,
    sourceUrl: audio?.getAttribute("src") || "",
  };
}

export function mediaUrlForFilename(filename: string): string {
  return encodeURIComponent(filename || "").replaceAll("%2F", "/");
}

function removeInstalledHandlers(handlers: InstalledAudioHandlers): void {
  handlers.audio.removeEventListener("loadedmetadata", handlers.loadedmetadata);
  handlers.audio.removeEventListener("ended", handlers.ended);
  handlers.audio.removeEventListener("error", handlers.error);
}

function currentRegistration(ord: number, audio: HTMLAudioElement): AudioRegistration | null {
  const registration = registrations.get(ord);
  return registration?.audio === audio ? registration : null;
}

async function mediaResponseStatusFor(src: string): Promise<number | null> {
  if (!src) return null;
  try {
    const response = await fetch(src, { cache: "no-store", method: "HEAD" });
    return response.status;
  } catch {
    return null;
  }
}

function audioBoundaryDurationMs(audio: HTMLAudioElement): number {
  return Math.max(audioDurationMs(audio), audioCurrentTimeMs(audio));
}

function audioDurationMs(audio: HTMLAudioElement): number {
  const durationSeconds = Number(audio.duration);
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) return 0;
  return Math.round(durationSeconds * 1000);
}

function audioCurrentTimeMs(audio: HTMLAudioElement): number {
  const currentSeconds = Number(audio.currentTime);
  if (!Number.isFinite(currentSeconds) || currentSeconds <= 0) return 0;
  return Math.round(currentSeconds * 1000);
}
