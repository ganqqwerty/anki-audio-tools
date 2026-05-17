/**
 * Structured logger for the settings UI.
 *
 * Always logs to the browser console at the appropriate level.
 * Also sends a `frontend_log` pycmd to Python (fire-and-forget, fails silently).
 *
 * Architecture rule TS-A: pycmd() is called here via the bridge module.
 * All other files must use this logger instead of console.log/warn/error.
 */

import type { FrontendLogPayload } from "./generated/contracts.js";
import { Level } from "./generated/contracts.js";
import { sendBridgeCommand } from "./bridge.js";

type LogLevel = "debug" | "info" | "warn" | "error";
type JsonLogValue = null | boolean | number | string | JsonLogValue[] | { [key: string]: JsonLogValue };
type LogSender = (payload: FrontendLogPayload) => void;

export interface ScopedLogger {
  debug: (message: string, context?: unknown) => void;
  error: (message: string, context?: unknown) => void;
  info: (message: string, context?: unknown) => void;
  warn: (message: string, context?: unknown) => void;
}

function consoleForLevel(level: LogLevel): typeof console.warn {
  if (level === "error") {
    return console.error;
  }
  return console.warn;
}

function generatedLevel(level: LogLevel): Level {
  if (level === "debug") return Level.Debug;
  if (level === "warn") return Level.Warn;
  if (level === "error") return Level.Error;
  return Level.Info;
}

function serializableContext(context: unknown, depth = 0): JsonLogValue {
  const scalar = serializableScalar(context);
  if (scalar !== undefined) return scalar;
  if (Array.isArray(context)) {
    return serializableArray(context, depth);
  }
  if (context !== null && typeof context === "object") {
    return serializableObject(context, depth);
  }
  return fallbackContextLabel(context);
}

function serializableScalar(context: unknown): JsonLogValue | undefined {
  if (context === undefined) return "[undefined]";
  if (context === null) return null;
  if (typeof context === "boolean" || typeof context === "number" || typeof context === "string") {
    return context;
  }
  return undefined;
}

function serializableArray(context: unknown[], depth: number): JsonLogValue {
  if (depth >= 4) return "[array]";
  return context.map((item) => serializableContext(item, depth + 1));
}

function serializableObject(context: object, depth: number): JsonLogValue {
  if (depth >= 4) return "[object]";
  const result: { [key: string]: JsonLogValue } = {};
  for (const [key, value] of Object.entries(context)) {
    result[key] = serializableContext(value, depth + 1);
  }
  return result;
}

function fallbackContextLabel(context: unknown): string {
  if (typeof context === "bigint") return context.toString();
  if (typeof context === "symbol") return context.description ? `Symbol(${context.description})` : "Symbol()";
  if (typeof context === "function") return `[function ${context.name || "anonymous"}]`;
  return "[unserializable]";
}

function payloadFor(level: LogLevel, message: string, context?: unknown): FrontendLogPayload {
  const payload: FrontendLogPayload = {
    level: generatedLevel(level),
    message,
  };
  if (context !== undefined) {
    payload.context = serializableContext(context);
  }
  return payload;
}

export function createLogger(scope: string, sendPayload: LogSender): ScopedLogger {
  function log(level: LogLevel, message: string, context?: unknown): void {
    const consoleFn = consoleForLevel(level);
    if (context === undefined) {
      consoleFn(`[${scope}] ${message}`);
    } else {
      consoleFn(`[${scope}] ${message}`, context);
    }

    try {
      sendPayload(payloadFor(level, message, context));
    } catch {
      // pycmd may not be available while the WebView is initializing.
    }
  }

  return {
    debug: (message: string, context?: unknown) => log("debug", message, context),
    error: (message: string, context?: unknown) => log("error", message, context),
    info: (message: string, context?: unknown) => log("info", message, context),
    warn: (message: string, context?: unknown) => log("warn", message, context),
  };
}

export const logger = createLogger("settings", (payload) => {
  sendBridgeCommand(`frontend_log:${JSON.stringify(payload)}`);
});
