/**
 * Tests for src/lib/logger.ts
 *
 * Verifies that:
 *  - logger.* logs to console (via console.warn / console.error)
 *  - logger.* sends a frontend_log pycmd (fire-and-forget)
 *  - pycmd failure is silently swallowed
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { logger } from "../src/lib/logger.js";

const pycmd = (globalThis as unknown as Record<string, ReturnType<typeof vi.fn>>)["pycmd"]!;

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

  it("logger sends frontend_log pycmd", () => {
    logger.info("test log");
    const calls = pycmd.mock.calls.filter((c) =>
      (c[0] as string).startsWith("frontend_log:")
    );
    expect(calls.length).toBeGreaterThan(0);
    const payload = JSON.parse(
      (calls[0]?.[0] as string).slice("frontend_log:".length)
    ) as { level: string; message: string };
    expect(payload.level).toBe("info");
    expect(payload.message).toBe("test log");
  });

  it("includes context in pycmd payload when provided", () => {
    logger.error("error with context", { code: 42 });
    const calls = pycmd.mock.calls.filter((c) =>
      (c[0] as string).startsWith("frontend_log:")
    );
    const payload = JSON.parse(
      (calls[0]?.[0] as string).slice("frontend_log:".length)
    ) as { level: string; message: string; context: unknown };
    expect(payload.context).toEqual({ code: 42 });
  });

  it("includes context in console output when provided", () => {
    logger.warn("warn with ctx", { extra: "data" });
    expect(warnSpy).toHaveBeenCalledWith("[settings] warn with ctx", {
      extra: "data",
    });
  });

  it("silently swallows pycmd failure", () => {
    pycmd.mockImplementationOnce(() => {
      throw new Error("pycmd unavailable");
    });
    expect(() => logger.info("safe call")).not.toThrow();
  });
});
