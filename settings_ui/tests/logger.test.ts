/**
 * Tests for src/lib/logger.ts
 *
 * Verifies that:
 *  - logger.* logs to console (via console.warn / console.error)
 *  - logger.* sends a frontend.log bridge command (fire-and-forget)
 *  - pycmd failure is silently swallowed
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { logger } from "../src/lib/logger.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;

function frontendLogPayload(): { level: string; message: string; scope: string; stack?: string; context?: unknown } {
  const call = pycmd.mock.calls
    .map(([command]) => command as string)
    .find((command) => command.startsWith("bridge:") && command.includes('"frontend.log"'));
  if (!call) {
    throw new Error("frontend.log bridge command was not sent");
  }
  const envelope = JSON.parse(call.slice("bridge:".length)) as {
    command: string;
    payload: { level: string; message: string; scope: string; stack?: string; context?: unknown };
  };
  expect(envelope.command).toBe("frontend.log");
  return envelope.payload;
}

describe("logger", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    warnSpy.mockRestore();
    errorSpy.mockRestore();
  });

  it("logger.debug logs to console.warn with [settings] prefix", () => {
    logger.debug("debug message");
    expect(warnSpy).toHaveBeenCalledWith("[settings] debug message");
  });

  it("logger.info logs to console.warn", () => {
    logger.info("info message");
    expect(warnSpy).toHaveBeenCalledWith("[settings] info message");
  });

  it("logger.warn logs to console.warn", () => {
    logger.warn("warn message");
    expect(warnSpy).toHaveBeenCalledWith("[settings] warn message");
  });

  it("logger.error logs to console.error", () => {
    logger.error("error message");
    expect(errorSpy).toHaveBeenCalledWith("[settings] error message");
  });

  it("logger sends frontend.log pycmd", () => {
    logger.info("test log");
    const payload = frontendLogPayload();
    expect(payload.level).toBe("info");
    expect(payload.message).toBe("test log");
    expect(payload.scope).toBe("settings");
  });

  it("includes context in pycmd payload when provided", () => {
    logger.error("error with context", { code: 42 });
    const payload = frontendLogPayload();
    expect(payload.context).toEqual({ code: 42 });
  });

  it("includes context in console output when provided", () => {
    logger.warn("warn with ctx", { extra: "data" });
    expect(warnSpy).toHaveBeenCalledWith("[settings] warn with ctx", {
      extra: "data",
    });
  });

  it("includes Error.stack in pycmd payload", () => {
    const error = new Error("render failed");
    logger.error("error with stack", error);

    const payload = frontendLogPayload();

    expect(payload.level).toBe("error");
    expect(payload.message).toBe("error with stack");
    expect(payload.stack).toContain("Error: render failed");
    expect(payload.context).toEqual({});
  });

  it("silently swallows pycmd failure", () => {
    pycmd.mockImplementationOnce(() => {
      throw new Error("pycmd unavailable");
    });
    expect(() => logger.info("safe call")).not.toThrow();
  });
});
