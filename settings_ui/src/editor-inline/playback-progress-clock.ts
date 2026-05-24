export interface PlaybackProgressPlan {
  endMs: number;
  playbackRate: number;
  startedAtMs: number;
  startMs: number;
}

export function playbackProgressPlan(
  startMs: number,
  endMs: number,
  startedAtMs: number,
  playbackRate = 1,
): PlaybackProgressPlan {
  const safeStartMs = finiteOrZero(startMs);
  const safeEndMs = Math.max(safeStartMs, finiteOrZero(endMs));
  const safeRate = playbackRate > 0 && Number.isFinite(playbackRate) ? playbackRate : 1;
  return {
    endMs: safeEndMs,
    playbackRate: safeRate,
    startedAtMs: finiteOrZero(startedAtMs),
    startMs: safeStartMs,
  };
}

export function progressMsForPlan(plan: PlaybackProgressPlan, nowMs: number): number {
  const elapsedMs = Math.max(0, finiteOrZero(nowMs) - plan.startedAtMs);
  return Math.min(plan.endMs, plan.startMs + elapsedMs * plan.playbackRate);
}

export function remainingMsForPlan(plan: PlaybackProgressPlan, nowMs: number): number {
  return Math.max(0, plan.endMs - progressMsForPlan(plan, nowMs));
}

function finiteOrZero(value: number): number {
  return Number.isFinite(value) ? value : 0;
}
