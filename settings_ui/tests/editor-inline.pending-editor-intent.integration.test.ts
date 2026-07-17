import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  AutoplayKind,
  SourceKind,
  type PendingEditorIntent,
} from "../src/lib/generated/contracts.js";
import {
  notifyPostEditPlaybackReady,
  rememberPostEditPlaybackIntent,
} from "../src/editor-inline/post-edit-playback.js";
import { setRepeatEnabledForOrd } from "../src/editor-inline/actions-playback.js";
import { readFieldState } from "../src/editor-inline/field-state-store.js";
import { readEditorPracticeSnapshot } from "../src/editor-inline/editor-practice-controller.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  commandLog,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  track,
} from "./editor-inline.integration.helpers.js";

describe("pending editor intent delivery", () => {
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

  it("starts autoplay frontend-locally and sends a terminal receipt", async () => {
    const pendingEditorIntent = intent("delivery-1");
    initializeEditorRuntime({ audioFieldIndices: [0], pendingEditorIntent });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    const audio = prepareHtmlAudio(0);

    notifyPostEditPlaybackReady(0, "clip one.mp3");
    await Promise.resolve();
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(receipts()).toEqual([
      expect.objectContaining({
        payload: expect.objectContaining({
          deliveryId: "delivery-1",
          editorSessionId: 7,
          outcome: "autoplay_accepted",
          schemaVersion: 1,
        }),
      }),
    ]);
    expect(commandLog()).not.toContain("aqe:post-edit-playback-ready");
  });

  it("deduplicates repeated readiness in one frontend runtime", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0], pendingEditorIntent: intent("delivery-2") });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    const audio = prepareHtmlAudio(0);

    notifyPostEditPlaybackReady(0, "clip one.mp3");
    notifyPostEditPlaybackReady(0, "clip one.mp3");
    await Promise.resolve();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(receipts()).toHaveLength(1);
  });

  it("rejects expired and source-mismatched deliveries without effects", async () => {
    const expired = intent("delivery-expired");
    expired.expiresAtEpochMs = Date.now() - 1;
    initializeEditorRuntime({ audioFieldIndices: [0], pendingEditorIntent: expired });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    const audio = prepareHtmlAudio(0);

    notifyPostEditPlaybackReady(0, "different.mp3");
    notifyPostEditPlaybackReady(0, "clip one.mp3");
    await Promise.resolve();

    expect(audio.play).not.toHaveBeenCalled();
    expect(receipts()).toEqual([]);
  });

  it("requests a rendered graph before accepting a generated-source intent", async () => {
    const pending = intent("delivery-graph");
    pending.autoplay.requireGraphRedraw = true;
    initializeEditorRuntime({ audioFieldIndices: [0], pendingEditorIntent: pending });
    scan(window.__AQE_EDITOR_CONFIG__!);

    notifyPostEditPlaybackReady(0, "clip one.mp3");
    await Promise.resolve();

    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toMatchObject({
      ord: 0,
      sourceFilename: "clip one.mp3",
    });
    expect(receipts()).toEqual([]);
  });

  it("retains repeat preference only across its exact pending-delivery remount", async () => {
    const backendEditorContext = {
      backendMediaGeneration: 3,
      editorSessionId: 7,
      noteId: 11,
    };
    initializeEditorRuntime({ audioFieldIndices: [0], backendEditorContext });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    expect(setRepeatEnabledForOrd(0, true)).toBe(true);
    expect(readFieldState(0).playback.repeat).toBe(true);
    const autoplay = rememberPostEditPlaybackIntent(0);
    const pendingEditorIntent = intent("delivery-repeat");
    pendingEditorIntent.autoplay = { ...pendingEditorIntent.autoplay, ...autoplay };
    disposeEditorRuntime();

    // Anki may mount once before Python attaches the generated delivery intent.
    // That intermediate runtime must not consume the identity-bound preference.
    initializeEditorRuntime({ audioFieldIndices: [0], backendEditorContext });
    disposeEditorRuntime();

    initializeEditorRuntime({
      audioFieldIndices: [0],
      backendEditorContext,
      pendingEditorIntent,
    });
    scan(window.__AQE_EDITOR_CONFIG__!);
    window.__aqeSetVisualizer?.(0, track, 0);
    const audio = prepareHtmlAudio(0);

    notifyPostEditPlaybackReady(0, "clip one.mp3");
    await Promise.resolve();
    await Promise.resolve();

    expect(readEditorPracticeSnapshot()?.state.kind).toBe("repeat");
    expect(readFieldState(0).playback.repeat).toBe(true);
    expect(audio.play).toHaveBeenCalledTimes(1);
  });
});

function intent(deliveryId: string): PendingEditorIntent {
  return {
    autoplay: {
      expectedDurationMs: 1000,
      kind: AutoplayKind.Once,
      repeatPauseMs: 0,
      requireGraphRedraw: false,
    },
    deliveryId,
    expiresAtEpochMs: Date.now() + 30_000,
    schemaVersion: 1,
    sourceKind: SourceKind.GeneratedEdit,
    target: {
      backendMediaGeneration: 3,
      editorSessionId: 7,
      fieldOrd: 0,
      noteId: 11,
      sourceFilename: "clip one.mp3",
    },
  };
}

function receipts(): Array<{ command: string; payload: Record<string, unknown> }> {
  return commandLog()
    .filter((command) => command.startsWith("bridge:"))
    .map((command) => JSON.parse(command.slice("bridge:".length)))
    .filter((envelope) => envelope.command === "editor.intent-receipt");
}
