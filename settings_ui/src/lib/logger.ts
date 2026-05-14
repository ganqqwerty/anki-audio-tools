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

function _log(level: LogLevel, message: string, context?: unknown): void {
  // Always log to console at the correct level
  const consoleFn =
    level === "debug"
      ? console.warn // jsdom / Anki webview don't have console.debug
      : level === "info"
        ? console.warn // promote info to warn so it shows in Anki console
        : level === "warn"
          ? console.warn
          : console.error;
  if (context !== undefined) {
    consoleFn(`[settings] ${message}`, context);
  } else {
    consoleFn(`[settings] ${message}`);
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
