import { describe, expect, it, vi } from "vitest";

import {
  encodeBridgeCommand,
  sendBridgeCommand,
} from "../src/lib/bridge.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;

describe("sendBridgeCommand", () => {
  it("forwards raw commands to pycmd", () => {
    sendBridgeCommand("test-command");
    expect(pycmd).toHaveBeenCalledWith("test-command");
  });

  it("retries until pycmd becomes available", () => {
    vi.useFakeTimers();
    const original = globalThis.pycmd;
    globalThis.pycmd = undefined;

    try {
      sendBridgeCommand("delayed-command");
      expect(pycmd).not.toHaveBeenCalled();

      globalThis.pycmd = pycmd;
      vi.advanceTimersByTime(25);

      expect(pycmd).toHaveBeenCalledWith("delayed-command");
    } finally {
      globalThis.pycmd = original;
      vi.useRealTimers();
    }
  });
});

describe("encodeBridgeCommand", () => {
  it("wraps commands in the shared JSON envelope", () => {
    expect(encodeBridgeCommand("settings.cancel")).toBe('bridge:{"command":"settings.cancel"}');
    expect(JSON.parse(encodeBridgeCommand("settings.save", { enabled: true }).slice("bridge:".length))).toEqual({
      command: "settings.save",
      payload: { enabled: true },
    });
  });
});
