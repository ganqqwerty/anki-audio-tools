import { describe, expect, it } from "vitest";

import type { PlaybackRegion } from "../src/editor-inline/playback-model.js";
import {
  chooseInitialActiveMarkerIndex,
  deriveActiveSuffix,
  emptySegmentPracticeState,
  markerNavigationAvailability,
  moveActiveMarkerIndex,
  normalizeSegmentMarkers,
  segmentControlAvailability,
  toggleSegmentMarker,
} from "../src/editor-inline/segment-practice-state.js";

const baseRegion: PlaybackRegion = {
  endMs: 2200,
  mode: "selection",
  startMs: 1000,
};

describe("editor inline segment practice state", () => {
  it("sorts, clamps, and deduplicates markers inside the base region", () => {
    expect(normalizeSegmentMarkers([1600.4, 100, 2200, 1600.2, 999.9, 1200], baseRegion)).toEqual([
      1000,
      1200,
      1600,
      2200,
    ]);
  });

  it("adds a marker when no nearby marker exists", () => {
    expect(toggleSegmentMarker([1200, 1900], 1500, baseRegion, 40)).toEqual({
      markersMs: [1200, 1500, 1900],
      removed: false,
    });
  });

  it("removes a nearby marker before adding a duplicate", () => {
    expect(toggleSegmentMarker([1200, 1500, 1900], 1518, baseRegion, 40)).toEqual({
      markersMs: [1200, 1900],
      removed: true,
    });
  });

  it("chooses the rightmost marker as the initial practice marker", () => {
    expect(chooseInitialActiveMarkerIndex([1200, 1500, 1900])).toBe(2);
    expect(chooseInitialActiveMarkerIndex([])).toBeNull();
  });

  it("moves next left toward longer suffixes and previous right toward shorter suffixes", () => {
    const markersMs = [1200, 1500, 1900];

    expect(moveActiveMarkerIndex(markersMs, 2, "next")).toBe(1);
    expect(moveActiveMarkerIndex(markersMs, 1, "next")).toBe(0);
    expect(moveActiveMarkerIndex(markersMs, 0, "next")).toBe(0);
    expect(moveActiveMarkerIndex(markersMs, 0, "previous")).toBe(1);
    expect(moveActiveMarkerIndex(markersMs, 2, "previous")).toBe(2);
  });

  it("derives the active suffix from the active marker to the stable base end", () => {
    expect(deriveActiveSuffix(baseRegion, [1200, 1500, 1900], 1)).toEqual({
      endMs: 2200,
      mode: "selection",
      startMs: 1500,
    });
    expect(deriveActiveSuffix(baseRegion, [1200, 1500, 1900], null)).toBeNull();
    expect(deriveActiveSuffix(null, [1200], 0)).toBeNull();
  });

  it("reports practice and navigation availability", () => {
    const stopped = emptySegmentPracticeState();
    expect(segmentControlAvailability(stopped)).toEqual({
      canClear: false,
      canEdit: false,
      canNext: false,
      canPractice: false,
      canPrevious: false,
    });

    const ready = {
      ...stopped,
      activeMarkerIndex: 2,
      baseRegion,
      markersMs: [1200, 1500, 1900],
    };
    expect(segmentControlAvailability(ready)).toEqual({
      canClear: true,
      canEdit: true,
      canNext: true,
      canPractice: true,
      canPrevious: false,
    });
    expect(markerNavigationAvailability([1200, 1500, 1900], 0)).toEqual({
      canNext: false,
      canPrevious: true,
    });
  });
});
