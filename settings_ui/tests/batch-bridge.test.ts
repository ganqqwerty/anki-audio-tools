import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  batchCancel,
  batchClose,
  batchCopyLog,
  batchStart,
  registerBatchCallbacks,
} from "../src/batch/bridge.js";
import { BatchOperationName } from "../src/lib/types.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;

describe("batch bridge", () => {
  beforeEach(() => {
    delete window.onBatchProgress;
    delete window.onBatchLog;
    delete window.onBatchFinish;
    delete window.onBatchError;
  });

  it("serializes batch commands through pycmd", () => {
    batchStart({
      operation: BatchOperationName.Graph,
      source_field: "Audio",
      target_field: "Image",
      parameters: {},
    });
    batchCancel();
    batchCopyLog();
    batchClose();

    expect(pycmd.mock.calls.map(([command]) => JSON.parse(String(command).slice("bridge:".length)))).toEqual([
      {
        command: "batch.start",
        payload: {
          operation: "graph",
          source_field: "Audio",
          target_field: "Image",
          parameters: {},
        },
      },
      { command: "batch.cancel" },
      { command: "batch.copy_log" },
      { command: "batch.close" },
    ]);
  });

  it("registers frontend callbacks", () => {
    const callbacks = {
      onProgress: vi.fn(),
      onLog: vi.fn(),
      onFinish: vi.fn(),
      onError: vi.fn(),
    };

    registerBatchCallbacks(callbacks);

    expect(window.onBatchProgress).toBe(callbacks.onProgress);
    expect(window.onBatchLog).toBe(callbacks.onLog);
    expect(window.onBatchFinish).toBe(callbacks.onFinish);
    expect(window.onBatchError).toBe(callbacks.onError);
  });
});
