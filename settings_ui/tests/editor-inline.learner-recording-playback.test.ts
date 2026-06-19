import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import { toggleLearnerRecordingHtmlPlayback } from "../src/editor-inline/learner-recording-playback.js";
import {
  bridgeCommands,
  mockAnimationFrames,
  muteConsole,
  renderFields,
  track,
} from "./editor-inline.integration.helpers.js";
import {
  initAndScan,
  recordingConfig,
  setupAudioTrack,
} from "./editor-inline.recording.integration.helpers.js";

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

  it("creates an HTML audio element with an encoded learner media URL", async () => {
    const playSpy = mockMediaPlayback();
    initAndScan(recordingConfig());
    await setupAudioTrack();
    publishReadyRecording({ mediaFilename: "voice recording.wav" });

    playRecordingButton().click();
    await flushMicrotasks();

    const audio = learnerAudio();
    expect(audio.getAttribute("src")).toBe("voice%20recording.wav");
    expect(playSpy).toHaveBeenCalledTimes(1);
    expect(bridgeCommands()).not.toContain("aqe:play-recording");
    expect(window.__aqeGraphStateForTest?.(0)?.learnerPlaybackStatus).toBe("playing");
    expect(playRecordingButton().dataset.aqeButtonState).toBe("pause");
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
  overrides: Partial<Parameters<NonNullable<typeof window.__aqeSetLearnerRecordingState>>[0]> = {},
): void {
  window.__aqeSetLearnerRecordingState?.({
    fieldOrd: 0,
    generation: 1,
    mediaFilename: "target__aqe_voice.wav",
    playbackStatus: "stopped",
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
  return document.querySelector<HTMLAudioElement>('[data-testid="aqe-learner-audio-0"]')!;
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
