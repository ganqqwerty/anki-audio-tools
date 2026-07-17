import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearAllHtmlAudioSessions,
  dispatchHtmlAudioSessionEvent,
  dispatchHtmlAudioSessionSourceFact,
  initializeHtmlAudioTransportRuntime,
  mountHtmlAudioTransportField,
  readActiveHtmlAudioTransportSnapshot,
  readHtmlAudioTransportFailureIdentity,
  readHtmlAudioTransportSourceIdentity,
  readHtmlAudioSessionState,
} from "../src/editor-inline/html-audio-session-controller.js";
import { executePlaybackRecovery } from "../src/editor-inline/playback-recovery-coordinator.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  bridgeEnvelopes,
  peekPendingCommandPayload,
  prepareHtmlAudio,
  renderFields,
} from "./editor-inline.integration.helpers.js";

describe("authoritative editor transport ownership", () => {
  beforeEach(() => {
    vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => undefined);
    vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => undefined);
    renderFields();
    const config = {
      audioFieldIndices: [0],
      backendEditorContext: {
        backendMediaGeneration: 4,
        editorSessionId: 7,
        mediaTargetsByField: {
          0: { backendMediaGeneration: 4, sourceFilename: "clip.m4a" },
        },
        noteId: 11,
      },
    };
    initializeEditorRuntime(config);
    scan(config);
  });

  afterEach(() => {
    disposeEditorRuntime();
    clearAllHtmlAudioSessions();
    vi.restoreAllMocks();
  });

  it.each([
    ["different filenames", "clip two.mp3"],
    ["the same filename", "clip one.mp3"],
  ])("keeps one active owner across two fields with %s", async (_label, secondFilename) => {
    disposeEditorRuntime();
    clearAllHtmlAudioSessions();
    document.body.innerHTML = `
      <audio data-testid="aqe-audio-clock-0"></audio>
      <audio data-testid="aqe-audio-clock-1"></audio>
    `;
    initializeHtmlAudioTransportRuntime();
    mountHtmlAudioTransportField(0);
    mountHtmlAudioTransportField(1);
    const firstAudio = prepareHtmlAudio(0);
    const secondAudio = prepareHtmlAudio(1);

    for (const [ord, sourceFilename] of [[0, "clip one.mp3"], [1, secondFilename]] as const) {
      dispatchHtmlAudioSessionEvent(ord, {
        cursorMs: 0,
        source: { kind: "source", sourceFilename },
        type: "SourceConfigured",
      });
      dispatchHtmlAudioSessionSourceFact(ord, readHtmlAudioTransportSourceIdentity(ord)!, {
        durationMs: 1000,
        type: "MetadataLoaded",
      });
    }
    start(0);
    await flushPlayback();
    start(1);
    await flushPlayback();

    expect(firstAudio.pause).toHaveBeenCalled();
    expect(readHtmlAudioSessionState(0).kind).not.toBe("playing");
    expect(readHtmlAudioSessionState(1).kind).toBe("playing");
    expect(readActiveHtmlAudioTransportSnapshot()).toMatchObject({ active: true, fieldOrd: 1 });
    expect(firstAudio.play).toHaveBeenCalledOnce();
    expect(secondAudio.play).toHaveBeenCalledOnce();
  });

  it("accepts only the current recovery failure once across same-filename replacement", () => {
    prepareHtmlAudio(0);
    failCurrentSource();
    const staleFailureIdentity = readHtmlAudioTransportFailureIdentity(0)!;
    const staleAction = {
      failureIdentity: staleFailureIdentity,
      fieldOrd: 0,
      kind: "convert_to_mp3" as const,
      sourceFilename: "clip.m4a",
    };
    failCurrentSource();
    const currentFailureIdentity = readHtmlAudioTransportFailureIdentity(0)!;
    const currentAction = { ...staleAction, failureIdentity: currentFailureIdentity };
    const actionNode = document.createElement("button");
    const recoveryCommands = () => bridgeEnvelopes("editor.source-mutation");

    expect(currentFailureIdentity.sourceInstanceId).not.toBe(staleFailureIdentity.sourceInstanceId);
    expect(executePlaybackRecovery(staleAction, actionNode)).toBe(false);
    expect(recoveryCommands()).toEqual([]);
    expect(peekPendingCommandPayload()).toBeNull();
    expect(executePlaybackRecovery(currentAction, actionNode)).toBe(true);
    expect(bridgeCommands()).toContain("focus:0");
    expect(recoveryCommands()).toHaveLength(1);
    expect(recoveryCommands()[0]).toMatchObject({
      command: "editor.source-mutation",
      payload: { kind: "convert_to_mp3", target: { sourceFilename: "clip.m4a" } },
    });
    expect(executePlaybackRecovery(currentAction, actionNode)).toBe(false);
    expect(recoveryCommands()).toHaveLength(1);
  });
});

function start(ord: number): void {
  dispatchHtmlAudioSessionEvent(ord, {
    request: {
      cursorMs: 0,
      endMs: 1000,
      loop: false,
      ord,
      regionMode: "full",
      source: "user",
    },
    type: "StartRequested",
  });
}

function failCurrentSource(): void {
  dispatchHtmlAudioSessionEvent(0, {
    cursorMs: 0,
    replace: true,
    source: { kind: "source", sourceFilename: "clip.m4a" },
    type: "SourceConfigured",
  });
  const identity = readHtmlAudioTransportSourceIdentity(0)!;
  dispatchHtmlAudioSessionSourceFact(0, identity, { durationMs: 1000, type: "MetadataLoaded" });
  dispatchHtmlAudioSessionSourceFact(0, identity, {
    cursorMs: 0,
    mediaErrorCode: 4,
    mediaResponseStatus: 200,
    reason: "audio_error",
    type: "AudioError",
  });
}

async function flushPlayback(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}
