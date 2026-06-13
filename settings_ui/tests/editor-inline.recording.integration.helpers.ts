import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { EditorButtonMode } from "../src/lib/types.js";
import type { EditorRuntimeConfig } from "../src/editor-inline/types.js";
import { track } from "./editor-inline.integration.helpers.js";

export function recordingConfig(): EditorRuntimeConfig {
  return {
    audioFieldIndices: [0],
    splitButtonDefaults: {
      denoiseAlgorithm: "standard" as const,
      pauseAggressiveness: "normal" as const,
      repeatPauseSeconds: 0,
      speedStep: 1.5,
      voiceRecordingCountdownSeconds: 0,
      volumeStepDb: 15,
    },
    visibleEditorButtons: [
      "aqe:analyze",
      "aqe:record-voice",
      "aqe:play-recording",
    ],
  };
}

export function recordingConfigWithCountdown(seconds: number): EditorRuntimeConfig {
  const config = recordingConfig();
  return {
    ...config,
    splitButtonDefaults: {
      ...config.splitButtonDefaults!,
      voiceRecordingCountdownSeconds: seconds,
    },
  };
}

export function textRecordingConfig(): EditorRuntimeConfig {
  return {
    ...recordingConfig(),
    editorButtonModes: {
      "aqe:play-recording": EditorButtonMode.Text,
      "aqe:record-voice": EditorButtonMode.Text,
    },
  };
}

export function setScrollbarDimensions(ord = 0, clientWidth = 500): HTMLDivElement {
  const scroller = document.querySelector<HTMLDivElement>(`[data-testid="aqe-time-scrollbar-scroll-${ord}"]`)!;
  Object.defineProperty(scroller, "clientWidth", { configurable: true, value: clientWidth });
  scroller.getBoundingClientRect = () => ({
    bottom: 16,
    height: 16,
    left: 0,
    right: clientWidth,
    top: 0,
    width: clientWidth,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  });
  return scroller;
}

export function initAndScan(config: EditorRuntimeConfig): void {
  initializeEditorRuntime(config);
  scan(config);
}

export async function setupAudioTrack(): Promise<void> {
  window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
  await Promise.resolve();
}
