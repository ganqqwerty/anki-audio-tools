import { repeatDefaultFromConfig } from "./control-actions.js";
import { visualizerForOrd } from "./dom-selectors.js";
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

function postEditPlaybackIntents(): Record<number, PostEditPlaybackIntent> {
  window.__aqePostEditPlaybackIntents ??= {};
  return window.__aqePostEditPlaybackIntents;
}

function normalizedRepeatPauseSeconds(value: number): number {
  if (!Number.isFinite(value) || value <= 0) return 0;
  return Math.min(10, value);
}
