import { visualizerForOrd } from "../src/editor-inline/dom-selectors.js";
import { initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import type { VisualizerElement } from "../src/editor-inline/types.js";
import { pycmdMock } from "./setup.js";

export const track = {
  analyzerName: "praat",
  durationMs: 1000,
  pitchMaxHz: 300,
  pitchMinHz: 100,
  points: [
    [0, 120, 0.1, true],
    [500, 180, 0.8, true],
    [1000, 220, 0.6, true],
  ],
  sourceFilename: "nested/clip two.mp3",
};

export async function mountTrack(cursorMs = 250): Promise<VisualizerElement> {
  document.body.innerHTML = `
    <div class="field-container" data-index="0">
      <div contenteditable="true" id="audio0">[sound:nested/clip two.mp3]</div>
    </div>
  `;
  initializeEditorRuntime({ audioFieldIndices: [0] });
  scan({ audioFieldIndices: [0] });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, cursorMs);
  const visualizer = visualizerForOrd(0);
  if (!visualizer) throw new Error("visualizer not mounted");
  return visualizer;
}

export function bridgeCommands(): string[] {
  return pycmdMock.mock.calls.map(([command]) => command);
}
