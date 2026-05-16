/**
 * Structured logger for the settings UI.
 *
 * Always logs to the browser console at the appropriate level.
 * Also sends a `frontend_log` pycmd to Python (fire-and-forget, fails silently).
 *
 * Architecture rule TS-A: pycmd() is called here via the bridge module.
 * All other files must use this logger instead of console.log/warn/error.
 */

import { sendBridgeCommand } from "./bridge.js";

type LogLevel = "debug" | "info" | "warn" | "error";

function consoleForLevel(level: LogLevel): typeof console.warn {
  if (level === "error") {
    return console.error;
  }
  return console.warn;
}

function _log(level: LogLevel, message: string, context?: unknown): void {
  const consoleFn = consoleForLevel(level);
  if (context === undefined) {
    consoleFn(`[settings] ${message}`);
  } else {
    consoleFn(`[settings] ${message}`, context);
  }

  // Fire-and-forget: send to Python logger (ignore failures)
  try {
    sendBridgeCommand(
      `frontend_log:${JSON.stringify({ level, message, context })}`,
    );
  } catch {
    // Silently ignore — pycmd may not be available yet
  }
}

export const logger = {
  debug: (message: string, context?: unknown) => _log("debug", message, context),
  info: (message: string, context?: unknown) => _log("info", message, context),
  warn: (message: string, context?: unknown) => _log("warn", message, context),
  error: (message: string, context?: unknown) => _log("error", message, context),
};
