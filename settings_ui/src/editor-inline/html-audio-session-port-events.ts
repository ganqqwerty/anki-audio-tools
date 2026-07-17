import { visualizerForOrd } from "./dom-selectors.js";
import { readFieldState, updateFieldState } from "./field-state-store.js";
import type { HtmlAudioPortCallbacks } from "./html-audio-session-audio-element.js";
import { publishLearnerPlaybackState } from "./html-audio-session-learner-projection.js";
import { resetCursorMsForRequest } from "./html-audio-session-resources.js";
import type { HtmlAudioSessionEvent, HtmlAudioSessionState } from "./html-audio-session-types.js";
import type {
  TransportAttemptIdentity,
  TransportSourceIdentity,
} from "./transport/index.js";
import { readTargetDurationMsForVisualizer, setTargetDurationMsForVisualizer } from "./visualizer-runtime-state.js";
import { renderCursor } from "./visualizer-renderer.js";

interface HtmlAudioPortEventDependencies {
  acceptsAttempt: (ord: number, identity: TransportAttemptIdentity) => boolean;
  dispatchAttemptFact: (
    ord: number,
    identity: TransportAttemptIdentity,
    event: HtmlAudioSessionEvent,
  ) => void;
  dispatchSourceFact: (
    ord: number,
    identity: TransportSourceIdentity,
    event: HtmlAudioSessionEvent,
  ) => void;
  readAttemptIdentity: (ord: number) => TransportAttemptIdentity | null;
  readState: (ord: number) => HtmlAudioSessionState;
}

/** Converts stable HTML media-port callbacks into identity-scoped transport facts. */
export function createHtmlAudioPortEventHandlers(
  dependencies: HtmlAudioPortEventDependencies,
): HtmlAudioPortCallbacks {
  return {
    currentAttemptIdentity: dependencies.readAttemptIdentity,
    onAudioError(ord, identity, cursorMs, mediaErrorCode, mediaResponseStatus) {
      const event: HtmlAudioSessionEvent = {
        cursorMs,
        mediaErrorCode,
        mediaResponseStatus,
        reason: "audio_error",
        type: "AudioError",
      };
      if ("attemptId" in identity) dependencies.dispatchAttemptFact(ord, identity, event);
      else dependencies.dispatchSourceFact(ord, identity, event);
    },
    onEnded(ord, identity, cursorMs) {
      if (!dependencies.acceptsAttempt(ord, identity)) return;
      const state = dependencies.readState(ord);
      if (state.kind !== "starting" && state.kind !== "playing") return;
      const learnerRecordingEnded = state.source.kind === "learner_recording";
      dependencies.dispatchAttemptFact(ord, identity, {
        cursorMs,
        resetCursorMs: resetCursorMsForRequest(state.request),
        type: "BoundaryReached",
      });
      if (learnerRecordingEnded) {
        publishLearnerPlaybackState(ord, "stopped", 0, dependencies.readState(ord));
      }
    },
    onMetadataLoaded(ord, identity, durationMs) {
      const field = readFieldState(ord);
      const visualizer = visualizerForOrd(ord);
      if (!field.graph.hasTrack) {
        updateFieldState(ord, (state) => ({
          ...state,
          graph: { ...state.graph, durationMs },
          playback: { ...state.playback, endMs: durationMs },
        }));
        if (visualizer) {
          if (readTargetDurationMsForVisualizer(visualizer, 0) <= 0) {
            setTargetDurationMsForVisualizer(visualizer, durationMs);
          }
          renderCursor(visualizer, readFieldState(ord).cursor.ms, durationMs);
        }
      }
      dependencies.dispatchSourceFact(ord, identity, { durationMs, type: "MetadataLoaded" });
    },
    onPlayRejected(ord, identity) {
      if (!dependencies.acceptsAttempt(ord, identity)) return;
      const state = dependencies.readState(ord);
      if (state.kind === "empty" || state.kind === "failed") return;
      dependencies.dispatchAttemptFact(ord, identity, {
        reason: "audio_play_rejected",
        sourceFilename: state.source.sourceFilename,
        type: "PlayRejected",
      });
    },
    onPlayResolved(ord, identity, nowMs) {
      if (!dependencies.acceptsAttempt(ord, identity)) return;
      const state = dependencies.readState(ord);
      if (state.kind === "empty" || state.kind === "failed") return;
      dependencies.dispatchAttemptFact(ord, identity, {
        nowMs,
        sourceFilename: state.source.sourceFilename,
        type: "PlayResolved",
      });
    },
    onSeekFailed(ord, identity, cursorMs) {
      dependencies.dispatchAttemptFact(ord, identity, {
        cursorMs,
        reason: "audio_seek_failed",
        type: "SeekFailed",
      });
    },
  };
}
