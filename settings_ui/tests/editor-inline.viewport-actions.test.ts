import { describe, expect, it } from "vitest";

import { playbackFollowViewport } from "../src/editor-inline/viewport-actions.js";

describe("editor inline viewport playback follow", () => {
  it("pans continuously at the right follow line instead of paging the cursor left", () => {
    const viewport = { startMs: 1000, endMs: 2000, durationMs: 4000 };

    expect(playbackFollowViewport(viewport, 1880)).toBeNull();
    expect(playbackFollowViewport(viewport, 1920)).toEqual({
      startMs: 1040,
      endMs: 2040,
      durationMs: 4000,
    });
  });

  it("reveals offscreen reset cursors with leading context", () => {
    expect(playbackFollowViewport({ startMs: 1400, endMs: 2000, durationMs: 4000 }, 500)).toEqual({
      startMs: 428,
      endMs: 1028,
      durationMs: 4000,
    });
  });
});
