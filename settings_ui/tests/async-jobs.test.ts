/**
 * Tests for src/lib/async-jobs.ts
 *
 * Verifies that startAsyncOp:
 *  - sends the correct async_cmd pycmd
 *  - returns a Promise that resolves when onAsyncDone fires with ok=true
 *  - returns a Promise that rejects when onAsyncDone fires with ok=false
 *  - calls the progress callback on onAsyncProgress
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import {
  _clearPendingForTest,
  handleAsyncDone,
  handleAsyncProgress,
  startAsyncOp,
} from "../src/lib/async-jobs.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;

afterEach(() => {
  _clearPendingForTest();
});

describe("startAsyncOp", () => {
  it("calls pycmd with async_cmd containing op and payload", () => {
    void startAsyncOp("health_check", {});
    const call = pycmd.mock.calls[0]?.[0] ?? "";
    expect(call).toMatch(/^async_cmd:/);
    const parsed = JSON.parse(call.slice("async_cmd:".length)) as {
      id: string;
      op: string;
      payload: unknown;
    };
    expect(parsed.op).toBe("health_check");
    expect(parsed.payload).toEqual({});
  });

  it("generates a unique id for each call", () => {
    void startAsyncOp("op_a", {});
    void startAsyncOp("op_b", {});
    const id1 = JSON.parse(
      (pycmd.mock.calls[0]?.[0] ?? "{}").slice("async_cmd:".length)
    ).id as string;
    const id2 = JSON.parse(
      (pycmd.mock.calls[1]?.[0] ?? "{}").slice("async_cmd:".length)
    ).id as string;
    expect(id1).not.toBe(id2);
  });

  it("promise resolves with result when onAsyncDone fires ok=true", async () => {
    const promise = startAsyncOp("health_check", {});
    const id = JSON.parse(
      (pycmd.mock.calls[0]?.[0] ?? "{}").slice("async_cmd:".length)
    ).id as string;

    handleAsyncDone({ id, ok: true, result: { response: "hello" } });

    const result = await promise;
    expect(result).toEqual({ response: "hello" });
  });

  it("promise rejects with error when onAsyncDone fires ok=false", async () => {
    const promise = startAsyncOp("health_check", {});
    const id = JSON.parse(
      (pycmd.mock.calls[0]?.[0] ?? "{}").slice("async_cmd:".length)
    ).id as string;

    handleAsyncDone({ id, ok: false, error: "API timeout" });

    await expect(promise).rejects.toThrow("API timeout");
  });

  it("calls onProgress callback with pct and message", () => {
    const onProgress = vi.fn();
    void startAsyncOp("fetch_voices", {}, onProgress);
    const id = JSON.parse(
      (pycmd.mock.calls[0]?.[0] ?? "{}").slice("async_cmd:".length)
    ).id as string;

    handleAsyncProgress({ id, progress: 50, message: "Fetching…" });
    expect(onProgress).toHaveBeenCalledWith(50, "Fetching…");
  });

  it("ignores onAsyncDone for unknown job ids", () => {
    expect(() => {
      handleAsyncDone({ id: "unknown-id", ok: true, result: {} });
    }).not.toThrow();
  });

  it("cleans up pending map after resolution", async () => {
    const promise = startAsyncOp("op", {});
    const id = JSON.parse(
      (pycmd.mock.calls[0]?.[0] ?? "{}").slice("async_cmd:".length)
    ).id as string;

    handleAsyncDone({ id, ok: true, result: null });
    await promise;

    // A second done with the same ID should be silently ignored
    expect(() => {
      handleAsyncDone({ id, ok: false, error: "late" });
    }).not.toThrow();
  });
});

describe("handleAsyncProgress", () => {
  it("silently ignores unknown job ids", () => {
    expect(() => {
      handleAsyncProgress({ id: "no-such-id", progress: 10, message: "x" });
    }).not.toThrow();
  });
});
