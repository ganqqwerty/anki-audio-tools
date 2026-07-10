import { describe, expect, it } from "vitest";

import type { PlaybackRegion } from "../src/editor-inline/playback-model.js";
import {
  activeMarkerIndexAfterMarkerToggle,
  chorusingControlAvailability,
  chooseInitialActiveMarkerIndex,
  defaultChorusingMarkers,
  deriveActiveSuffix,
  emptyChorusingState,
  markerNavigationAvailability,
  moveActiveMarkerIndex,
  normalizeChorusingMarkers,
  toggleChorusingMarker,
} from "../src/editor-inline/chorusing-state";

const baseRegion: PlaybackRegion = {
  endMs: 2200,
  mode: "selection",
  startMs: 1000,
};

describe("editor inline chorusing state", () => {
  it("sorts, clamps, and deduplicates markers inside the base region", () => {
    expect(normalizeChorusingMarkers([1600.4, 100, 2200, 1600.2, 999.9, 1200], baseRegion)).toEqual([
      1000,
      1200,
      1600,
      2200,
    ]);
  });

  it("creates default markers from the selection start at the configured interval", () => {
    expect(defaultChorusingMarkers(baseRegion, 500)).toEqual([1000, 1500, 2000]);
  });

  it("clamps invalid default marker intervals to the built-in default", () => {
    expect(defaultChorusingMarkers(baseRegion, Number.NaN)).toEqual([1000, 1500, 2000]);
    expect(defaultChorusingMarkers(baseRegion, 10)).toEqual([
      1000,
      1050,
      1100,
      1150,
      1200,
      1250,
      1300,
      1350,
      1400,
      1450,
      1500,
      1550,
      1600,
      1650,
      1700,
      1750,
      1800,
      1850,
      1900,
      1950,
      2000,
      2050,
      2100,
      2150,
    ]);
  });

  it("adds a marker when no nearby marker exists", () => {
    expect(toggleChorusingMarker([1200, 1900], 1500, baseRegion, 40)).toEqual({
      markersMs: [1200, 1500, 1900],
      removed: false,
    });
  });

  it("removes a nearby marker before adding a duplicate", () => {
    expect(toggleChorusingMarker([1200, 1500, 1900], 1518, baseRegion, 40)).toEqual({
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

  it("normalizes the active marker after inserting before the current marker", () => {
    expect(activeMarkerIndexAfterMarkerToggle([0, 500, 750], [0, 250, 500, 750], 1)).toBe(2);
  });

  it("normalizes the active marker after inserting after the current marker", () => {
    expect(activeMarkerIndexAfterMarkerToggle([0, 500, 750], [0, 500, 625, 750], 1)).toBe(1);
  });

  it("normalizes the active marker after removing the current marker", () => {
    expect(activeMarkerIndexAfterMarkerToggle([0, 500, 750], [0, 750], 1)).toBe(1);
  });

  it("normalizes the active marker to null when all markers are removed", () => {
    expect(activeMarkerIndexAfterMarkerToggle([500], [], 0)).toBeNull();
  });

  it("reports whole-file marker and navigation availability", () => {
    const stopped = emptyChorusingState();
    expect(chorusingControlAvailability(stopped)).toEqual({
      canNext: false,
      canPrevious: false,
      canPractice: false,
    });

    const ready = {
      ...stopped,
      baseRegion,
      markersMs: [1200, 1500, 1900],
    };
    expect(chorusingControlAvailability(ready, {
      endMs: 2200,
      mode: "selection",
      startMs: 1900,
    })).toEqual({
      canNext: true,
      canPrevious: false,
      canPractice: true,
    });
    expect(markerNavigationAvailability([1200, 1500, 1900], 0)).toEqual({
      canNext: false,
      canPrevious: true,
    });
  });
});
