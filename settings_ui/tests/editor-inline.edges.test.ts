import { describe, expect, it } from "vitest";

import {
  audioClockReady,
  clearStatus,
  seekAudioClock,
  setControlsBusy,
  setStatus,
  setVisualizer,
  setVisualizerStatus,
} from "../src/editor-inline/actions.js";
import {
  popPendingPlaybackRequest,
  sendBridgeCommand,
  setPendingPlaybackRequest,
} from "../src/editor-inline/bridge.js";
import {
  cursorMsFromEvent,
  drawLabels,
  drawPitch,
  drawXAxis,
  graphPixelBounds,
  pathForIntensity,
  yForPitch,
} from "../src/editor-inline/plot.js";
import {
  audioSourceForNode,
  explicitFieldTargets,
  fieldIndex,
  fieldNodes,
} from "../src/editor-inline/runtime.js";
import { isPlaybackState, normalizeTrack } from "../src/editor-inline/types.js";
import { pycmdMock } from "./setup.js";

describe("editor inline defensive edges", () => {
  it("keeps bridge helpers safe without pycmd and without pending playback", () => {
    const globalWithPycmd = globalThis as unknown as { pycmd: ((cmd: string) => void) | undefined };
    const original = globalWithPycmd.pycmd;
    globalWithPycmd.pycmd = undefined;

    expect(() => sendBridgeCommand("aqe:play")).not.toThrow();
    expect(popPendingPlaybackRequest()).toBeNull();
    setPendingPlaybackRequest({ action: "start", cursorMs: 1, ord: 2 });
    expect(popPendingPlaybackRequest()).toEqual({ action: "start", cursorMs: 1, ord: 2 });
    expect(popPendingPlaybackRequest()).toBeNull();

    globalWithPycmd.pycmd = original;
    sendBridgeCommand("aqe:play");
    expect(pycmdMock).toHaveBeenCalledWith("aqe:play");
  });

  it("normalizes invalid payload values and playback state strings", () => {
    const track = normalizeTrack({
      analyzerName: "fallback",
      durationMs: Number.NaN,
      pitchMaxHz: null,
      pitchMinHz: null,
      points: [[false, true, null, "nope" as unknown as boolean]],
      sourceFilename: "bad.wav",
    });

    expect(track.durationMs).toBe(0);
    expect(track.points[0]).toEqual([0, null, null, false]);
    expect(isPlaybackState("playing")).toBe(true);
    expect(isPlaybackState("other")).toBe(false);
  });

  it("covers plot guard branches and missing SVG groups", () => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.getBoundingClientRect = () => ({
      bottom: 0,
      height: 0,
      left: 0,
      right: 0,
      top: 0,
      width: 0,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });
    const visualizer = document.createElement("div");

    expect(pathForIntensity([], 1000)).toBe("");
    expect(yForPitch(200, 300, 100)).toBe(116);
    expect(graphPixelBounds(svg)).toEqual({ left: 44, width: 566 });
    expect(cursorMsFromEvent({ clientX: -100 }, svg, 1000)).toBe(0);
    expect(() => drawPitch(visualizer, {
      analyzerName: "",
      durationMs: 0,
      pitchMaxHz: null,
      pitchMinHz: null,
      points: [],
      sourceFilename: "",
    })).not.toThrow();
    expect(() => drawLabels(visualizer, {
      analyzerName: "",
      durationMs: 0,
      pitchMaxHz: null,
      pitchMinHz: null,
      points: [],
      sourceFilename: "",
    })).not.toThrow();
    expect(() => drawXAxis(visualizer, 0)).not.toThrow();
  });

  it("handles scanner/index fallbacks and unsupported audio references", () => {
    document.body.innerHTML = `
      <div class="field-container" data-index="4">[sound:fallback.mp3]</div>
      <div class="field-container" data-index="5"></div>
      <div class="field-container" data-index="6">[sound:container.mp3]<div contenteditable="true"></div></div>
      <div contenteditable="true" id="field-7">[sound:unsupported.flac]</div>
      <div contenteditable="true" data-ord="8">text</div>
      <div contenteditable="true">duplicate</div>
      <div contenteditable="true">duplicate</div>
    `;
    const explicit = explicitFieldTargets([4]);

    expect(explicit).toHaveLength(1);
    expect(explicit[0]?.sourceFilename).toBe("fallback.mp3");
    expect(explicitFieldTargets([5], { 5: "note-source.wav" })[0]?.sourceFilename).toBe("note-source.wav");
    expect(explicitFieldTargets([6])[0]?.sourceFilename).toBe("container.mp3");
    expect(audioSourceForNode(document.getElementById("field-7")!)).toBe("");
    expect(fieldIndex(document.getElementById("field-7")!, 0)).toBe(7);
    expect(fieldIndex(document.querySelector<HTMLElement>("[data-ord]")!, 0)).toBe(8);
    expect(fieldNodes().length).toBeGreaterThan(1);
  });

  it("returns safely when controls, visualizers, or audio clocks are absent", () => {
    document.body.innerHTML = "";

    expect(audioClockReady(null)).toBe(false);
    expect(seekAudioClock(document.createElement("div"), 10)).toBe(false);
    expect(() => setControlsBusy(9, true, "Busy")).not.toThrow();
    expect(() => setStatus("No active field")).not.toThrow();
    expect(() => clearStatus(9)).not.toThrow();
    expect(() => setVisualizerStatus(9, "Missing")).not.toThrow();
    expect(() => setVisualizer(9, {
      analyzerName: "",
      durationMs: 0,
      pitchMaxHz: null,
      pitchMinHz: null,
      points: [],
      sourceFilename: "",
    }, 0)).not.toThrow();
  });
});
