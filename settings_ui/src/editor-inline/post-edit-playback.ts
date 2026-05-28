import { sendBridgeCommand } from "./bridge.js";
import { allControls, visualizerForOrd } from "./dom-selectors.js";
import type { PostEditPlaybackIntent } from "./types.js";

export function rememberPostEditPlaybackIntent(ord: number): void {
  const visualizer = visualizerForOrd(ord);
  postEditPlaybackIntents()[ord] = {
    repeat: visualizer ? visualizer.dataset.repeatEnabled === "true" : repeatDefaultFromConfig(),
    repeatPauseSeconds: normalizedRepeatPauseSeconds(
      visualizer ? Number(visualizer.dataset.repeatPauseSeconds || "0") : 0,
    ),
  };
}

export function consumePostEditPlaybackIntent(ord: number): PostEditPlaybackIntent | null {
  const intents = postEditPlaybackIntents();
  const intent = intents[ord] ?? null;
  if (intent) {
    delete intents[ord];
  }
  return intent;
}

export function notifyPostEditPlaybackReady(ord: number, sourceFilename: string): void {
  const pending = window.__AQE_EDITOR_CONFIG__?.pendingPostEditPlayback;
  if (!pending || pending.fieldOrd !== ord) return;
  if (pending.sourceFilename && pending.sourceFilename !== sourceFilename) return;
  if (document.body.dataset.aqeBusy === "true") return;
  if (!postEditPlaybackGraphReady(ord, sourceFilename)) return;
  window.__aqePendingCommandPayload = {
    command: "aqe:post-edit-playback-ready",
    fieldOrd: ord,
    generation: pending.generation,
    sourceFilename,
  };
  sendBridgeCommand("aqe:command-payload");
}

function postEditPlaybackGraphReady(ord: number, sourceFilename: string): boolean {
  const pending = window.__AQE_EDITOR_CONFIG__?.pendingPostEditPlayback;
  if (!pending?.requireGraphRedraw) return true;
  const expectedSource = window.__aqePendingGraphRedrawField === ord ? window.__aqePendingGraphRedrawSource || "" : "";
  const sourceToMatch = expectedSource || pending.sourceFilename || sourceFilename;
  const visualizer = visualizerForOrd(ord);
  return !!visualizer
    && visualizer.dataset.graphBusy !== "true"
    && visualizer.dataset.hasTrack === "true"
    && (!sourceToMatch || visualizer.dataset.sourceFilename === sourceToMatch);
}

export function notifyMountedPostEditPlaybackReady(): void {
  allControls().forEach((controls) => {
    notifyPostEditPlaybackReady(
      Number(controls.dataset.aqeFieldOrd || "0"),
      controls.dataset.aqeSourceFilename || "",
    );
  });
}

function postEditPlaybackIntents(): Record<number, PostEditPlaybackIntent> {
  window.__aqePostEditPlaybackIntents ??= {};
  return window.__aqePostEditPlaybackIntents;
}

function normalizedRepeatPauseSeconds(value: number): number {
  if (!Number.isFinite(value) || value <= 0) return 0;
  return Math.min(10, value);
}

function repeatDefaultFromConfig(): boolean {
  return window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;
}
