import {
  SourceMutationCommandKind,
  type SourceMutationCommand,
} from "../lib/generated/contracts.js";
import { sendBridgeCommand, sendBridgeEnvelope } from "../lib/bridge-transport.js";
import { editorRuntimeConfig } from "./editor-runtime-config.js";
import { claimHtmlAudioPlaybackRecovery } from "./html-audio-session-controller.js";
import { logger } from "./logger.js";
import type { PlaybackRecoveryAction } from "./playback-recovery-types.js";

/** Atomically claim the current failed transport snapshot before mutating its source. */
export function executePlaybackRecovery(
  action: PlaybackRecoveryAction,
  node: HTMLElement,
): boolean {
  const backend = editorRuntimeConfig().backendEditorContext;
  const mediaTarget = backend?.mediaTargetsByField?.[action.fieldOrd];
  if (!backend || !mediaTarget || mediaTarget.sourceFilename !== action.sourceFilename) {
    logger.warn("transport.recovery_missing_backend_target", {
      failureId: action.failureIdentity.failureId,
      ord: action.fieldOrd,
    });
    return false;
  }
  if (!claimHtmlAudioPlaybackRecovery(action)) {
    logger.debug("transport.recovery_stale_or_duplicate", {
      failureId: action.failureIdentity.failureId,
      ord: action.fieldOrd,
      sourceFilename: action.sourceFilename,
    });
    return false;
  }
  node.focus?.();
  window.__aqeActiveField = action.fieldOrd;
  const command: SourceMutationCommand = {
    failure: {
      attemptId: action.failureIdentity.attemptId === null
        ? "none"
        : String(action.failureIdentity.attemptId),
      failureId: String(action.failureIdentity.failureId),
      fieldInstanceId: String(action.failureIdentity.fieldInstanceId),
      runtimeId: String(action.failureIdentity.runtimeId),
      sourceInstanceId: String(action.failureIdentity.sourceInstanceId),
    },
    kind: SourceMutationCommandKind.ConvertToMp3,
    schemaVersion: 1,
    target: {
      backendMediaGeneration: mediaTarget.backendMediaGeneration,
      editorSessionId: backend.editorSessionId,
      fieldOrd: action.fieldOrd,
      noteId: backend.noteId,
      sourceFilename: action.sourceFilename,
    },
  };
  sendBridgeCommand(`focus:${action.fieldOrd}`);
  sendBridgeEnvelope("editor.source-mutation", command);
  return true;
}
