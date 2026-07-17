import { describe, expect, it } from "vitest";

import type { HtmlAudioSessionEvent } from "../src/editor-inline/html-audio-session-types.js";
import {
  eventInterruptsEffectBatch,
  transportIdentityScopeFor,
  type TransportIdentityScope,
} from "../src/editor-inline/transport/event-policy.js";

const source = { kind: "source" as const, sourceFilename: "clip.mp3" };
const request = {
  cursorMs: 0,
  endMs: 1000,
  loop: false,
  ord: 0,
  regionMode: "full" as const,
  source: "user" as const,
};

const events = [
  [{ cursorMs: 0, mediaErrorCode: null, mediaResponseStatus: null, reason: "audio_error", type: "AudioError" }, "source", true],
  [{ cursorMs: 1000, type: "BoundaryReached" }, "attempt", false],
  [{ durationMs: 1000, type: "MetadataLoaded" }, "source", false],
  [{ type: "MetadataTimeout" }, "source", false],
  [{ cursorMs: 0, type: "PauseRequested" }, "runtime", true],
  [{ reason: "audio_play_rejected", sourceFilename: "clip.mp3", type: "PlayRejected" }, "attempt", false],
  [{ nowMs: 1, sourceFilename: "clip.mp3", type: "PlayResolved" }, "attempt", false],
  [{ type: "RecoveryClaimed" }, "source", false],
  [{ type: "ResumeRequested" }, "runtime", false],
  [{ type: "RuntimeDisposed" }, "runtime", true],
  [{ cursorMs: 0, reason: "audio_seek_failed", type: "SeekFailed" }, "attempt", true],
  [{ type: "SourceCleared" }, "runtime", true],
  [{ cursorMs: 0, source, type: "SourceConfigured" }, "runtime", true],
  [{ request, type: "StartRequested" }, "runtime", true],
  [{ cursorMs: 0, type: "StopRequested" }, "runtime", true],
] satisfies ReadonlyArray<readonly [HtmlAudioSessionEvent, TransportIdentityScope, boolean]>;

describe("transport event policy", () => {
  it.each(events)("assigns %s to the declared identity scope", (event, scope, _interrupts) => {
    expect(transportIdentityScopeFor(event)).toBe(scope);
  });

  it.each(events)("classifies whether %s interrupts the current effect batch", (event, _scope, interrupts) => {
    expect(eventInterruptsEffectBatch(event)).toBe(interrupts);
  });
});
