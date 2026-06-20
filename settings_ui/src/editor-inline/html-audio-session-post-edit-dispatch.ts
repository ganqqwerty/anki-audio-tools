import { sendCommandPayload } from "./bridge.js";
import { logger } from "./logger.js";
import type { EditorCommandPayload } from "./types.js";

const postEditReadyDispatches = new Set<string>();

export function clearPostEditReadyDispatches(): void {
  postEditReadyDispatches.clear();
}

export function dispatchPostEditReady(payload: EditorCommandPayload): void {
  const dispatchKey = postEditReadyDispatchKey(payload);
  if (dispatchKey && postEditReadyDispatches.has(dispatchKey)) {
    logger.info("post-edit playback ready duplicate suppressed", {
      fieldOrd: payload.fieldOrd,
      generation: "generation" in payload ? payload.generation : undefined,
      sourceFilename: "sourceFilename" in payload ? payload.sourceFilename : undefined,
    });
    return;
  }
  if (dispatchKey) {
    postEditReadyDispatches.add(dispatchKey);
  }
  const dispatch = () => {
    sendCommandPayload(payload);
    logger.info("post-edit playback ready dispatched", {
      fieldOrd: payload.fieldOrd,
      generation: "generation" in payload ? payload.generation : undefined,
      sourceFilename: "sourceFilename" in payload ? payload.sourceFilename : undefined,
    });
  };
  if (window.__aqeDispatchPostEditPlaybackReadyForTest?.(payload, dispatch) === true) return;
  dispatch();
}

function postEditReadyDispatchKey(payload: EditorCommandPayload): string | null {
  if (payload.command !== "aqe:post-edit-playback-ready") return null;
  return `${payload.fieldOrd}\u0000${payload.generation}\u0000${payload.sourceFilename}`;
}
