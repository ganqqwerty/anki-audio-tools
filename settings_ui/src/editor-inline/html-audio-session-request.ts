import type { HtmlAudioStartRequest } from "./html-audio-session-types.js";

export function htmlAudioLoopStartMs(request: HtmlAudioStartRequest): number {
  return Math.round(request.resetCursorMs ?? request.cursorMs);
}

export function htmlAudioRequestCoversFullSource(request: HtmlAudioStartRequest, durationMs: number): boolean {
  return htmlAudioLoopStartMs(request) <= 0
    && durationMs > 0
    && request.endMs >= Math.max(0, durationMs - 20);
}
