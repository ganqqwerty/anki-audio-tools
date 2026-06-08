import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { mediaUrlForFilename } from "../src/editor-inline/audio-clock.js";
import { processingMessage } from "../src/editor-inline/commands.js";
import { commandSlugsForTest } from "../src/editor-inline/test-contract.js";
import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import { commandButtons } from "../src/lib/editor-toolbar-buttons.js";

describe("editor inline action workflows", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    disposeEditorRuntime();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("encodes media names while preserving nested Anki media paths", () => {
    expect(mediaUrlForFilename("hello world.mp3")).toBe("hello%20world.mp3");
    expect(mediaUrlForFilename("かな.wav")).toBe("%E3%81%8B%E3%81%AA.wav");
    expect(mediaUrlForFilename("nested/clip.mp3")).toBe("nested/clip.mp3");
    expect(mediaUrlForFilename("hash#question?percent%.opus")).toBe("hash%23question%3Fpercent%25.opus");
    expect(mediaUrlForFilename('quote"line\nback\\slash.ogg')).toBe("quote%22line%0Aback%5Cslash.ogg");
    expect(commandSlugsForTest()["aqe:denoise-standard"]).toBe("denoise-standard");
    expect(commandSlugsForTest()["aqe:rnnoise"]).toBe("rnnoise");
    expect(commandSlugsForTest()["aqe:dpdfnet"]).toBe("dpdfnet");
    expect(commandSlugsForTest()["aqe:voice-only"]).toBe("voice-only");
    expect(commandSlugsForTest()["aqe:convert"]).toBe("convert");
    expect(commandSlugsForTest()["aqe:chorusing-practice"]).toBe("chorusing-practice");
    expect(commandSlugsForTest()["aqe:chorusing-previous"]).toBe("chorusing-previous");
    expect(commandSlugsForTest()["aqe:chorusing-next"]).toBe("chorusing-next");
    expect(commandSlugsForTest()["aqe:redo"]).toBe("redo");
    expect(commandSlugsForTest()["aqe:settings"]).toBe("settings");
    expect(commandButtons().find((button) => button.command === "aqe:chorusing-practice")?.icon).toBe("bug-play");
    expect(processingMessage("aqe:denoise-standard")).toBe("Denoising with Standard...");
    expect(processingMessage("aqe:rnnoise")).toBe("Denoising with RNNoise...");
    expect(processingMessage("aqe:dpdfnet")).toBe("Denoising with DPDFNet...");
    expect(processingMessage("aqe:voice-only")).toBe("Separating vocals with Spleeter...");
    expect(
      processingMessage("aqe:convert", {
        command: "aqe:convert",
        fieldOrd: 0,
        overrides: { targetFormat: "flac" },
      }),
    ).toBe("Converting to FLAC...");
    expect(processingMessage("aqe:faster")).toBe("Processing...");
  });
});
