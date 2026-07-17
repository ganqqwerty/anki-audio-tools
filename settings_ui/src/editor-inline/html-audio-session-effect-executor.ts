import { t } from "../lib/i18n.js";
import { setStatusForOrd, type EditorStatusMessage } from "./control-actions.js";
import { renderPlaybackWarning } from "./control-status-renderer.js";
import { stableStatusState } from "./editor-control-state.js";
import {
  failPendingEditorIntentForOrd,
} from "./editor-intent-controller.js";
import type { HtmlAudioElementOperations } from "./html-audio-session-audio-element.js";
import { completePlayback, publishPlaybackState } from "./html-audio-session-field-projection.js";
import type { HtmlAudioSessionResources } from "./html-audio-session-resources.js";
import type { HtmlAudioSessionEffect, HtmlAudioSessionState, HtmlAudioStartRequest } from "./html-audio-session-types.js";
import { logger } from "./logger.js";
import type { TransportAttemptIdentity, TransportFailureIdentity, TransportSourceIdentity } from "./transport/index.js";

interface HtmlAudioSessionEffectDependencies {
  audio: HtmlAudioElementOperations;
  readAttemptIdentity: (ord: number) => TransportAttemptIdentity;
  readFailureIdentity: (ord: number) => TransportFailureIdentity;
  readRequest: (ord: number) => HtmlAudioStartRequest | null;
  readSourceIdentity: (ord: number) => TransportSourceIdentity;
  readState: (ord: number) => HtmlAudioSessionState;
  reportPassCompleted: (ord: number, request: HtmlAudioStartRequest) => boolean;
  resources: HtmlAudioSessionResources;
}

/** Executes reducer effects through narrow ports without retaining transport state. */
export function createHtmlAudioSessionEffectExecutor(dependencies: HtmlAudioSessionEffectDependencies) {
  return (ord: number, effect: HtmlAudioSessionEffect): boolean => {
    switch (effect.type) {
      case "ConfigureAudioSource":
        dependencies.audio.configureAudioSource(ord, effect.sourceFilename, dependencies.readSourceIdentity(ord)); return false;
      case "SeekAudio": dependencies.audio.seekAudio(ord, effect.cursorMs, dependencies.readAttemptIdentity(ord)); return false;
      case "ReloadAudioSource": dependencies.audio.reloadAudioSource(ord, dependencies.readAttemptIdentity(ord)); return false;
      case "PlayAudio": dependencies.audio.playAudio(ord, dependencies.readAttemptIdentity(ord)); return false;
      case "PauseAudio": dependencies.audio.pauseAudio(ord); return false;
      case "ClearAudioSource": dependencies.audio.clearAudioSource(ord); return false;
      case "StartProgressFrame": dependencies.resources.startProgressFrame(ord, effect.cursorMs, effect.endMs); return false;
      case "ClearProgressFrame": dependencies.resources.clearProgressFrame(ord); return false;
      case "StartMetadataTimer": dependencies.resources.startMetadataTimer(ord, effect.timeoutMs); return false;
      case "ClearMetadataTimer": dependencies.resources.clearMetadataTimer(ord); return false;
      case "PublishPlaybackState":
        publishPlaybackState({
          cursorMs: effect.cursorMs,
          ord,
          request: dependencies.readRequest(ord),
          session: dependencies.readState(ord),
          status: effect.status,
        }); return false;
      case "CompletePlayback":
        completePlayback(ord, effect.cursorMs, dependencies.readRequest(ord)?.source === "post_edit"); return false;
      case "ReportPassCompleted": return dependencies.reportPassCompleted(ord, effect.request);
      case "ShowPlaybackStatus":
        if (effect.preserveStableError && stableStatusState(ord).kind === "error") return false;
        setStatusForOrd(
          ord,
          playbackStatusMessage(ord, effect, dependencies.readFailureIdentity),
          effect.kind ?? "warning",
          "",
          effect.kind === "error" ? "error" : "playback",
        ); return false;
      case "ShowPostEditPlaybackWarning":
        failPendingEditorIntentForOrd(ord);
        renderPlaybackWarning(ord, playbackStatusMessage(ord, effect, dependencies.readFailureIdentity)); return false;
      case "LogPlaybackTelemetry": logger.debug(effect.event, { ...effect.data, ord }); return false;
      default: return exhaustive(effect);
    }
  };
}

function playbackStatusMessage(
  ord: number,
  effect: Extract<HtmlAudioSessionEffect, { type: "ShowPlaybackStatus" | "ShowPostEditPlaybackWarning" }>,
  readFailureIdentity: (ord: number) => TransportFailureIdentity,
): EditorStatusMessage {
  const message = t(effect.statusKey);
  const recovery = effect.recovery
    ? { ...effect.recovery, failureIdentity: readFailureIdentity(ord) }
    : undefined;
  return effect.statusCode
    ? { code: effect.statusCode, message, ...(recovery ? { recovery } : {}) }
    : message;
}

function exhaustive(value: never): never {
  throw new Error(`Unhandled html audio session effect: ${JSON.stringify(value)}`);
}
