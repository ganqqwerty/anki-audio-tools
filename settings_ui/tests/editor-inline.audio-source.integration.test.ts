import { describe, expect, it } from "vitest";

import { audioSourceForNode } from "../src/editor-inline/runtime.js";

describe("editor inline audio source detection", () => {
  it.each(["aac", "flac", "m4a", "mp3", "oga", "ogg", "opus", "wav", "webm"])(
    "detects %s sound references as supported audio",
    (extension) => {
      document.body.innerHTML = `<div id="format-field">[sound:clip one.${extension.toUpperCase()}]</div>`;

      expect(audioSourceForNode(document.getElementById("format-field")!)).toBe(
        `clip one.${extension.toUpperCase()}`,
      );
    },
  );

  it("does not detect mp4 sound references as supported audio", () => {
    document.body.innerHTML = '<div id="video-field">[sound:clip.mp4]</div>';

    expect(audioSourceForNode(document.getElementById("video-field")!)).toBe("");
  });

  it("detects utf sound references as supported audio", () => {
    document.body.innerHTML = '<div id="utf-field">[sound:Даии_青山 voice.OPUS]</div>';

    expect(audioSourceForNode(document.getElementById("utf-field")!)).toBe("Даии_青山 voice.OPUS");
  });

  it("detects entity-escaped bracket filenames from field text", () => {
    document.body.innerHTML = '<div id="special-field">[sound:amp&amp;bracket]name.OPUS]</div>';

    expect(audioSourceForNode(document.getElementById("special-field")!)).toBe("amp&bracket]name.OPUS");
  });

  it("preserves trailing whitespace after supported audio extensions", () => {
    document.body.innerHTML = '<div id="trailing-field">[sound:clip.opus ]</div>';

    expect(audioSourceForNode(document.getElementById("trailing-field")!)).toBe("clip.opus ");
  });

  it("preserves mixed trailing dots and spaces after supported audio extensions", () => {
    document.body.innerHTML = '<div id="trailing-mixed-field">[sound:clip.opus .]</div>';

    expect(audioSourceForNode(document.getElementById("trailing-mixed-field")!)).toBe("clip.opus .");
  });
});
