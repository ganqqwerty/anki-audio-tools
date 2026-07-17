import { describe, expect, it } from "vitest";

import type { HtmlAudioSessionState } from "../src/editor-inline/html-audio-session-types.js";
import {
  validateTransportOwnership,
  validateTransportResources,
  validateTransportState,
} from "../src/editor-inline/transport/index.js";

const source = { kind: "source" as const, sourceFilename: "clip.mp3" };
const request = {
  cursorMs: 0,
  endMs: 1000,
  loop: false,
  ord: 0,
  regionMode: "full" as const,
  source: "user" as const,
};

describe("transport invariant validators", () => {
  type ActiveState = Extract<HtmlAudioSessionState, { kind: "starting" | "playing" | "paused" }>;

  const activeState = (kind: ActiveState["kind"], ord = 0): ActiveState => {
    const base = { durationMs: 1000, kind, ord, request: { ...request, ord }, source };
    if (kind === "playing") return { ...base, kind, startedAtMs: 1 };
    if (kind === "paused") return { ...base, kind, pausedAtMs: 250 };
    return { ...base, kind };
  };

  it("T-01 rejects two active fields", () => {
    const playing = (ord: number): HtmlAudioSessionState => ({
      durationMs: 1000,
      kind: "playing",
      ord,
      request: { ...request, ord },
      source,
      startedAtMs: 1,
    });
    expect(validateTransportOwnership(new Map([[0, playing(0)]]))).toEqual([]);
    expect(validateTransportOwnership(new Map([[0, playing(0)], [1, playing(1)]])))
      .toEqual([{ invariantId: "T-01", message: "multiple fields own active transport state" }]);
    expect(validateTransportOwnership(new Map([
      [0, { cursorMs: 0, durationMs: 1000, kind: "ready", ord: 0, source }],
      [1, { cursorMs: 0, durationMs: 1000, kind: "ready", ord: 1, source }],
    ]))).toEqual([]);
  });

  it("T-02 rejects invalid field, duration, and pass coordinates", () => {
    expect(validateTransportState({ cursorMs: 0, kind: "empty", ord: -1 }))
      .toEqual([{ invariantId: "T-02", message: "transport field ordinal is invalid" }]);
    expect(validateTransportState({ cursorMs: 0, durationMs: 0, kind: "ready", ord: 0, source }))
      .toEqual([{ invariantId: "T-02", message: "ready transport has no media duration" }]);
    expect(validateTransportState({
      durationMs: 1000,
      kind: "starting",
      ord: 0,
      request: { ...request, cursorMs: 1000 },
      source,
    })).toEqual([{ invariantId: "T-02", message: "starting transport has invalid pass coordinates" }]);
    expect(validateTransportState({ cursorMs: 0, kind: "empty", ord: 0.5 }))
      .toEqual([{ invariantId: "T-02", message: "transport field ordinal is invalid" }]);
  });

  it.each(["ready", "starting", "playing", "paused"] as const)(
    "T-02 requires positive duration in %s state",
    (kind) => {
      const state: HtmlAudioSessionState = kind === "ready"
        ? { cursorMs: 0, durationMs: 0, kind, ord: 0, source }
        : { ...activeState(kind), durationMs: 0 };
      expect(validateTransportState(state)).toEqual([
        { invariantId: "T-02", message: `${kind} transport has no media duration` },
      ]);
    },
  );

  it.each(["starting", "playing", "paused"] as const)(
    "T-02 validates both pass coordinate boundaries in %s state",
    (kind) => {
      expect(validateTransportState({
        ...activeState(kind),
        request: { ...request, cursorMs: -1 },
      })).toEqual([{ invariantId: "T-02", message: `${kind} transport has invalid pass coordinates` }]);
      expect(validateTransportState({
        ...activeState(kind),
        request: { ...request, cursorMs: 500, endMs: 500 },
      })).toEqual([{ invariantId: "T-02", message: `${kind} transport has invalid pass coordinates` }]);
    },
  );

  it("accepts valid inactive and active states", () => {
    expect(validateTransportState({ cursorMs: 0, kind: "empty", ord: 0 })).toEqual([]);
    expect(validateTransportState({ cursorMs: 0, kind: "loading", ord: 0, pendingStart: null, source })).toEqual([]);
    expect(validateTransportState({ cursorMs: 0, durationMs: 1000, kind: "ready", ord: 0, source })).toEqual([]);
    for (const kind of ["starting", "playing", "paused"] as const) {
      expect(validateTransportState(activeState(kind))).toEqual([]);
    }
  });

  it("T-04 rejects resources retained by states that cannot own them", () => {
    const ready: HtmlAudioSessionState = {
      cursorMs: 0,
      durationMs: 1000,
      kind: "ready",
      ord: 0,
      source,
    };
    expect(validateTransportResources(ready, {
      hasMetadataTimer: false,
      hasProgressFrame: false,
    })).toEqual([]);
    expect(validateTransportResources(ready, {
      hasMetadataTimer: true,
      hasProgressFrame: true,
    })).toEqual([
      { invariantId: "T-04", message: "terminal transport retains progress frame" },
      { invariantId: "T-04", message: "terminal transport retains metadata timer" },
    ]);
  });

  it("T-04 permits only the resources owned by loading and active playback", () => {
    const loading: HtmlAudioSessionState = {
      cursorMs: 0, kind: "loading", ord: 0, pendingStart: null, source,
    };
    expect(validateTransportResources(loading, {
      hasMetadataTimer: true,
      hasProgressFrame: false,
    })).toEqual([]);
    for (const kind of ["starting", "playing"] as const) {
      expect(validateTransportResources(activeState(kind), {
        hasMetadataTimer: false,
        hasProgressFrame: true,
      })).toEqual([]);
    }
    expect(validateTransportResources(activeState("paused"), {
      hasMetadataTimer: false,
      hasProgressFrame: true,
    })).toEqual([{ invariantId: "T-04", message: "terminal transport retains progress frame" }]);
  });

  it.each(["starting", "playing", "paused"] as const)("T-01 counts %s as active", (kind) => {
    expect(validateTransportOwnership(new Map([
      [0, activeState(kind, 0)],
      [1, activeState(kind, 1)],
    ]))).toEqual([{ invariantId: "T-01", message: "multiple fields own active transport state" }]);
  });
});
