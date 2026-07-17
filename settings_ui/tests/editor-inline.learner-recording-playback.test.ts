import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import { toggleLearnerRecordingHtmlPlayback } from "../src/editor-inline/learner-recording-playback.js";
import { readHtmlAudioSessionState } from "../src/editor-inline/html-audio-session-controller.js";
import { handleHtmlPlaybackCommand } from "../src/editor-inline/playback-actions.js";
import {
  bridgeCommands,
  mockAnimationFrames,
  muteConsole,
  publishRecorderSnapshot,
  renderFields,
  track,
} from "./editor-inline.integration.helpers.js";
import {
  initAndScan,
  recordingConfig,
  setupAudioTrack,
} from "./editor-inline.recording.integration.helpers.js";

const nativeDispatchEvent = EventTarget.prototype.dispatchEvent;

describe("editor inline learner recording HTML playback", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("does not call the bridge when no ready recording exists", async () => {
    initAndScan(recordingConfig());
    await setupAudioTrack();

    expect(toggleLearnerRecordingHtmlPlayback(0)).toBe(true);

    expect(bridgeCommands()).not.toContain("aqe:play-recording");
    expect(document.querySelector('[data-testid="aqe-learner-audio-0"]')).toBeNull();
    expect(document.querySelector<HTMLElement>(".aqe-status")).toHaveTextContent(
      "The referenced audio file was not found in Anki's media folder.",
    );
  });

  it("plays learner recording through the shared HTML audio session", async () => {
    const playSpy = mockMediaPlayback();
    initAndScan(recordingConfig());
    await setupAudioTrack();
    publishReadyRecording({ mediaFilename: "voice recording.wav" });

    playRecordingButton().click();
    await flushMicrotasks();

    const audio = learnerAudio();
    expect(audio.getAttribute("src")).toBe("voice%20recording.wav");
    expect(playSpy).toHaveBeenCalledTimes(1);
    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "playing",
      source: {
        kind: "learner_recording",
        sourceFilename: "voice recording.wav",
      },
    });
    expect(bridgeCommands()).not.toContain("aqe:play-recording");
    expect(window.__aqeGraphStateForTest?.(0)?.learnerPlaybackStatus).toBe("playing");
    expect(playRecordingButton().dataset.aqeButtonState).toBe("pause");
  });

  it("keeps main playback on the original field audio after a recording is ready", async () => {
    const playSpy = mockMediaPlayback();
    initAndScan({
      ...recordingConfig(),
      visibleEditorButtons: [
        "aqe:play",
        "aqe:analyze",
        "aqe:record-voice",
        "aqe:play-recording",
      ],
    });
    await setupAudioTrack();
    publishReadyRecording({ mediaFilename: "voice recording.wav" });

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "ready",
      source: {
        kind: "learner_recording",
        sourceFilename: "voice recording.wav",
      },
    });
    const audio = learnerAudio();
    Object.defineProperty(audio, "duration", { configurable: true, value: 1 });
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    expect(handleHtmlPlaybackCommand(0)).toBe(true);
    audio.dispatchEvent(new Event("loadedmetadata"));
    await flushMicrotasks();

    expect(playSpy).toHaveBeenCalledTimes(1);
    expect(audio.getAttribute("src")).toBe("clip%20one.mp3");
    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "playing",
      source: {
        kind: "source",
        sourceFilename: "clip one.mp3",
      },
    });
    expect(bridgeCommands()).not.toContain("aqe:play");
  });

  it("renders progress at the learner start cursor plus current audio time", async () => {
    mockMediaPlayback();
    const frames = mockAnimationFrames();
    initAndScan(recordingConfig());
    await setupAudioTrack();
    publishReadyRecording({ recordingDurationMs: 600, startCursorMs: 200 });

    playRecordingButton().click();
    await flushMicrotasks();
    const audio = learnerAudio();
    audio.currentTime = 0.25;

    frames.shift()?.(performance.now() + 16);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 450,
      progressMs: 450,
    });
  });

  it("pauses and resumes learner recording playback in HTML", async () => {
    const playSpy = mockMediaPlayback();
    const pauseSpy = vi.spyOn(window.HTMLMediaElement.prototype, "pause").mockImplementation(() => undefined);
    initAndScan(recordingConfig());
    await setupAudioTrack();
    publishReadyRecording({ recordingDurationMs: 600, startCursorMs: 200 });

    playRecordingButton().click();
    await flushMicrotasks();
    learnerAudio().currentTime = 0.3;
    pauseSpy.mockClear();

    playRecordingButton().click();
    await Promise.resolve();
    expect(pauseSpy).toHaveBeenCalledTimes(1);
    expect(window.__aqeGraphStateForTest?.(0)?.learnerPlaybackStatus).toBe("paused");
    expect(window.__aqeGraphStateForTest?.(0)?.cursorMs).toBe(500);

    playRecordingButton().click();
    await flushMicrotasks();
    expect(playSpy).toHaveBeenCalledTimes(2);
    expect(window.__aqeGraphStateForTest?.(0)?.learnerPlaybackStatus).toBe("playing");
  });

  it("resets learner playback state when audio ends", async () => {
    mockMediaPlayback();
    initAndScan(recordingConfig());
    await setupAudioTrack();
    publishReadyRecording({ recordingDurationMs: 600, startCursorMs: 200 });

    playRecordingButton().click();
    await flushMicrotasks();
    learnerAudio().dispatchEvent(new Event("ended"));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 200,
      learnerPlaybackStatus: "stopped",
    });
    expect(playRecordingButton().dataset.aqeButtonState).toBe("default");
  });

  it("does not patch EventTarget dispatch globally for learner playback", async () => {
    mockMediaPlayback();
    initAndScan(recordingConfig());
    await setupAudioTrack();
    publishReadyRecording({ recordingDurationMs: 600, startCursorMs: 200 });

    playRecordingButton().click();
    await flushMicrotasks();

    expect(EventTarget.prototype.dispatchEvent).toBe(nativeDispatchEvent);
    learnerAudio().dispatchEvent(new Event("ended"));
    expect(window.__aqeGraphStateForTest?.(0)?.learnerPlaybackStatus).toBe("stopped");
  });

  it("stops without bridge fallback when browser play rejects", async () => {
    vi.spyOn(window.HTMLMediaElement.prototype, "play").mockImplementation(() => Promise.reject(new Error("blocked")));
    vi.spyOn(window.HTMLMediaElement.prototype, "pause").mockImplementation(() => undefined);
    initAndScan(recordingConfig());
    await setupAudioTrack();
    publishReadyRecording({ mediaFilename: "voice recording.wav", recordingDurationMs: 600 });

    playRecordingButton().click();
    await flushMicrotasks();

    expect(bridgeCommands()).not.toContain("aqe:play-recording");
    expect(window.__aqeGraphStateForTest?.(0)?.learnerPlaybackStatus).toBe("stopped");
    expect(document.querySelector<HTMLElement>(".aqe-status")).toHaveTextContent("Browser audio is unavailable.");
  });
});

function publishReadyRecording(
  overrides: Parameters<typeof publishRecorderSnapshot>[0] = {},
): void {
  publishRecorderSnapshot({
    attemptId: 1,
    fieldOrd: 0,
    mediaFilename: "target__aqe_voice.wav",
    recordingDurationMs: 500,
    startCursorMs: 0,
    status: "ready",
    targetDurationMs: track.durationMs,
    ...overrides,
  });
}

function playRecordingButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play-recording"]')!;
}

function learnerAudio(): HTMLAudioElement {
  return document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
}

function mockMediaPlayback(): ReturnType<typeof vi.spyOn> {
  vi.spyOn(window.HTMLMediaElement.prototype, "pause").mockImplementation(() => undefined);
  return vi.spyOn(window.HTMLMediaElement.prototype, "play").mockImplementation(() => Promise.resolve());
}

async function flushMicrotasks(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
}
