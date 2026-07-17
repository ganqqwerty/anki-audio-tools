import { formatRepeatPauseSeconds } from "../lib/audio-operation-parameters.js";
import { t } from "../lib/i18n.js";
import { setButtonTooltipContent } from "../lib/rich-tooltip.js";
import {
  playRepeatMenuButtonForOrd,
  repeatControlsForOrd,
} from "./dom-selectors.js";
import { readFieldState, writeFieldState } from "./field-state-store.js";
import type { VisualizerElement } from "./types.js";
import { readRepeatPauseSecondsRuntime } from "./visualizer-runtime-state.js";

function fieldOrd(v: VisualizerElement): number {
  return Number(v.dataset.aqeFieldOrd || "0");
}

export function projectRepeatEnabled(visualizer: VisualizerElement, enabled: boolean): void {
  const ord = fieldOrd(visualizer);
  const current = readFieldState(ord);
  writeFieldState(ord, {
    ...current,
    playback: { ...current.playback, repeat: enabled },
  });
  for (const control of repeatControlsForOrd(ord)) {
    control.checked = enabled;
  }
  const menuButton = playRepeatMenuButtonForOrd(ord);
  if (!menuButton) return;
  const pause = formatRepeatPauseSeconds(readRepeatPauseSecondsRuntime(visualizer));
  const title = t("editor.play.menu_title", {
    value: t("editor.play.current_value", {
      pause,
      repeat: enabled ? t("editor.play.repeat_on") : t("editor.play.repeat_off"),
    }),
  });
  setButtonTooltipContent(menuButton, title);
}

export function repeatEnabledFor(visualizer: VisualizerElement): boolean {
  return readFieldState(fieldOrd(visualizer)).playback.repeat;
}
