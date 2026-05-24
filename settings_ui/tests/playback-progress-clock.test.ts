import { describe, expect, it } from "vitest";

import {
  playbackProgressPlan,
  progressMsForPlan,
  remainingMsForPlan,
} from "../src/editor-inline/playback-progress-clock.js";

describe("playback progress clock", () => {
  it("reports deterministic progress from the plan start time", () => {
    const plan = playbackProgressPlan(0, 1000, 5000);

    expect(progressMsForPlan(plan, 5000)).toBe(0);
    expect(progressMsForPlan(plan, 5500)).toBe(500);
    expect(progressMsForPlan(plan, 6500)).toBe(1000);
  });

  it("handles non-zero starts and selected-region boundaries", () => {
    const plan = playbackProgressPlan(250, 750, 1000);

    expect(progressMsForPlan(plan, 1100)).toBe(350);
    expect(progressMsForPlan(plan, 2000)).toBe(750);
    expect(remainingMsForPlan(plan, 1100)).toBe(400);
    expect(remainingMsForPlan(plan, 2000)).toBe(0);
  });

  it("uses a default 1x playback rate and clamps invalid ranges", () => {
    const plan = playbackProgressPlan(900, 700, 1000, 0);

    expect(plan.playbackRate).toBe(1);
    expect(plan.endMs).toBe(900);
    expect(progressMsForPlan(plan, 1500)).toBe(900);
  });
});
