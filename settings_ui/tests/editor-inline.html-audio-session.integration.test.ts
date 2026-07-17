import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearHtmlAudioSession,
  clearAllHtmlAudioSessions,
  dispatchHtmlAudioSessionEvent,
  dispatchHtmlAudioSessionSourceFact,
  readHtmlAudioPortSnapshot,
  readHtmlAudioTransportSourceIdentity,
  readHtmlAudioTransportPosition,
  readHtmlAudioSessionState,
} from "../src/editor-inline/html-audio-session-controller.js";
import { setStatusForOrd } from "../src/editor-inline/control-actions.js";
import { readFieldState } from "../src/editor-inline/field-state-store.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  mockAnimationFrames,
  prepareHtmlAudio,
  renderFields,
} from "./editor-inline.integration.helpers.js";

function dispatchCurrentSourceFact(
  event: Parameters<typeof dispatchHtmlAudioSessionSourceFact>[2],
): void {
  const identity = readHtmlAudioTransportSourceIdentity(0);
  if (!identity) throw new Error("expected current transport source identity");
  dispatchHtmlAudioSessionSourceFact(0, identity, event);
}

describe("editor inline html audio session controller", () => {
  beforeEach(() => {
    vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => undefined);
    vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => undefined);
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
  });

  afterEach(() => {
    disposeEditorRuntime();
    clearAllHtmlAudioSessions();
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("stores source playback session state between events", async () => {
    const audio = prepareHtmlAudio(0);

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 0,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "starting",
      source: { kind: "source", sourceFilename: "clip one.mp3" },
    });
    expect(readFieldState(0).playback.state).toBe("stopped");

    await Promise.resolve();
    await Promise.resolve();

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "playing",
      ord: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
    });
    expect(audio.play).toHaveBeenCalledOnce();
  });

  it("reads port readiness without evaluating a recursive media duration getter", () => {
    const audio = prepareHtmlAudio(0);
    const readDuration = vi.fn(() => 1);
    Object.defineProperty(audio, "duration", {
      configurable: true,
      get: readDuration,
    });

    expect(readHtmlAudioPortSnapshot(0)).toMatchObject({
      currentTimeMs: 0,
      present: true,
      readyState: 1,
    });
    expect(readDuration).not.toHaveBeenCalled();
  });

  it("publishes interpolated transport position while media currentTime lags", async () => {
    const frames = mockAnimationFrames();
    let nowMs = 0;
    vi.spyOn(performance, "now").mockImplementation(() => nowMs);
    const audio = prepareHtmlAudio(0);

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({ durationMs: 1000, type: "MetadataLoaded" });
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 0,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });
    await Promise.resolve();
    await Promise.resolve();

    nowMs = 300;
    frames.shift()?.(nowMs);

    expect(audio.currentTime).toBe(0);
    expect(readHtmlAudioTransportPosition(0)).toBe(300);
  });

  it("stores failed and stopped state when source playback is rejected", async () => {
    const audio = prepareHtmlAudio(0);
    audio.play = vi.fn<() => Promise<void>>(() => Promise.reject(new Error("blocked")));

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 250,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });

    await Promise.resolve();
    await Promise.resolve();

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      cursorMs: 250,
      kind: "failed",
      reason: "audio_play_rejected",
      source: { kind: "source", sourceFilename: "clip one.mp3" },
    });
    expect(readFieldState(0).playback.state).toBe("stopped");
    expect(audio.pause).toHaveBeenCalled();
  });

  it("stops the outer start effects when seeking fails synchronously", () => {
    const audio = prepareHtmlAudio(0);
    Object.defineProperty(audio, "currentTime", {
      configurable: true,
      get: () => 0,
      set: () => {
        throw new Error("seek failed");
      },
    });

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 250,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      cursorMs: 250,
      kind: "failed",
      reason: "audio_seek_failed",
      source: { kind: "source", sourceFilename: "clip one.mp3" },
    });
    expect(readFieldState(0).playback.state).toBe("stopped");
    expect(audio.play).not.toHaveBeenCalled();
  });

  it("stops the outer start effects when audio is missing during play", () => {
    const audio = prepareHtmlAudio(0);

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    audio.remove();
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 250,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      cursorMs: 250,
      kind: "failed",
      reason: "audio_play_rejected",
      source: { kind: "source", sourceFilename: "clip one.mp3" },
    });
    expect(readFieldState(0).playback.state).toBe("stopped");
    expect(audio.play).not.toHaveBeenCalled();
  });

  it("surfaces unclassified audio element errors without claiming the media is missing", async () => {
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    audio.play = vi.fn<() => Promise<void>>(() => new Promise(() => undefined));
    audio.pause = vi.fn<() => void>(() => undefined);

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "missing.mp3" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 0,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });

    audio.dispatchEvent(new Event("error"));

    await vi.waitFor(() => expect(readHtmlAudioSessionState(0).kind).toBe("failed"));

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "failed",
      reason: "audio_error",
    });
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Browser audio is unavailable.",
    );
  });

  it("offers MP3 recovery when Chromium reports an unsupported M4A source", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ status: 200 }));
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    audio.play = vi.fn<() => Promise<void>>(() => new Promise(() => undefined));
    audio.pause = vi.fn<() => void>(() => undefined);
    Object.defineProperty(audio, "error", {
      configurable: true,
      value: { code: 4 },
    });

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip.m4a" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({ durationMs: 1000, type: "MetadataLoaded" });
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 0,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });

    audio.dispatchEvent(new Event("error"));

    await vi.waitFor(() => expect(readHtmlAudioSessionState(0).kind).toBe("failed"));

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "failed",
      mediaErrorCode: 4,
      mediaResponseStatus: 200,
      reason: "audio_error",
    });
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "AQE-PLAYBACK-002: This audio format cannot be played in Audio Quick Editor. Help Convert to MP3",
    );
    expect(document.querySelector('[data-testid="aqe-convert-to-mp3-0"]')).toBeInstanceOf(HTMLButtonElement);
  });

  it("preserves an edit error when passive media readiness fails later", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ status: 200 }));
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "error", {
      configurable: true,
      value: { code: 4 },
    });
    setStatusForOrd(
      0,
      { code: "AQE-AUDIO-001", message: "Transform failed." },
      "error",
      "",
      "error",
    );
    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "invalid.wav" },
      type: "SourceConfigured",
    });

    audio.dispatchEvent(new Event("error"));

    await vi.waitFor(() => expect(readHtmlAudioSessionState(0).kind).toBe("failed"));
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "AQE-AUDIO-001: Transform failed. Help",
    );
  });

  it("keeps the error code paired with a delayed route response after metadata races", async () => {
    let resolveFetch = (_value: { status: number }): void => undefined;
    vi.stubGlobal("fetch", vi.fn(() => new Promise((resolve) => {
      resolveFetch = resolve;
    })));
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "error", { configurable: true, value: { code: 4 } });

    audio.dispatchEvent(new Event("error"));
    audio.dispatchEvent(new Event("loadedmetadata"));
    resolveFetch({ status: 200 });

    await vi.waitFor(() => expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "failed",
      mediaResponseStatus: 200,
    }));
    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "failed",
      mediaErrorCode: 4,
    });
  });

  it("keeps recovery actionable when post-edit autoplay restores an unsupported source", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ status: 200 }));
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "error", { configurable: true, value: { code: 4 } });
    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "restored.m4a" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({ durationMs: 1000, type: "MetadataLoaded" });
    dispatchHtmlAudioSessionEvent(0, {
      request: { cursorMs: 0, endMs: 1000, loop: false, ord: 0, regionMode: "full", source: "post_edit" },
      type: "StartRequested",
    });

    audio.dispatchEvent(new Event("error"));

    await vi.waitFor(() => expect(readHtmlAudioSessionState(0).kind).toBe("failed"));
    expect(document.querySelector('[data-testid="aqe-playback-warning-0"]')).toHaveTextContent(
      "AQE-PLAYBACK-002: The edited audio format cannot be played in Audio Quick Editor. Help Convert to MP3",
    );
    expect(document.querySelector('[data-testid="aqe-convert-to-mp3-0"]')).toBeInstanceOf(HTMLButtonElement);
  });

  it("ignores a stale play resolve after same-filename source replacement", async () => {
    let resolvePlay = (): void => {
      throw new Error("play promise was not created");
    };
    const audio = prepareHtmlAudio(0);
    audio.play = vi.fn<() => Promise<void>>(() => new Promise((resolve) => {
      resolvePlay = resolve;
    }));

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });
    dispatchCurrentSourceFact({
      durationMs: 1000,
      type: "MetadataLoaded",
    });
    dispatchHtmlAudioSessionEvent(0, {
      request: {
        cursorMs: 0,
        endMs: 1000,
        loop: false,
        ord: 0,
        regionMode: "full",
        source: "user",
      },
      type: "StartRequested",
    });
    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 125,
      replace: true,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });

    resolvePlay();
    await Promise.resolve();
    await Promise.resolve();

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      cursorMs: 125,
      kind: "loading",
      source: { kind: "source", sourceFilename: "clip one.mp3" },
    });
  });

  it("clearHtmlAudioSession pauses audio and removes source", () => {
    const audio = prepareHtmlAudio(0);

    dispatchHtmlAudioSessionEvent(0, {
      cursorMs: 0,
      source: { kind: "source", sourceFilename: "clip one.mp3" },
      type: "SourceConfigured",
    });
    expect(audio.getAttribute("src")).toBe("clip%20one.mp3");

    clearHtmlAudioSession(0);

    expect(audio.pause).toHaveBeenCalled();
    expect(audio.getAttribute("src")).toBeNull();
    expect(audio.src).toBe("");
    expect(readHtmlAudioSessionState(0)).toEqual({ kind: "empty", ord: 0, cursorMs: 0 });
  });

});
