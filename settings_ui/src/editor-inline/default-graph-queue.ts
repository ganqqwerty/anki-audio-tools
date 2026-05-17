import {
  controlsForOrd,
  visualizerForOrd,
} from "./dom-selectors.js";
import type { DefaultGraphTarget } from "./types.js";

export interface DefaultGraphQueueDependencies {
  anyBusy: () => boolean;
  requestDefaultGraph: (target: DefaultGraphTarget) => void;
}

interface QueuedDefaultGraph {
  key: string;
  ord: number;
  sourceFilename: string;
}

const queue: QueuedDefaultGraph[] = [];
const requestedKeys = new Set<string>();
let activeKey: string | null = null;
let activeOrd: number | null = null;
let retryScheduled = false;

export function clearDefaultGraphQueue(): void {
  queue.length = 0;
  requestedKeys.clear();
  activeKey = null;
  activeOrd = null;
  retryScheduled = false;
}

export function enqueueDefaultGraphs(
  targets: readonly DefaultGraphTarget[],
  dependencies: DefaultGraphQueueDependencies,
): void {
  for (const target of targets) {
    if (!target.sourceFilename) continue;
    const key = defaultGraphKey(target);
    if (requestedKeys.has(key)) continue;
    const visualizer = visualizerForOrd(target.ord);
    if (
      visualizer?.dataset.hasTrack === "true"
      && visualizer.dataset.sourceFilename === target.sourceFilename
    ) {
      requestedKeys.add(key);
      continue;
    }
    requestedKeys.add(key);
    queue.push({ key, ord: target.ord, sourceFilename: target.sourceFilename });
  }
  continueDefaultGraphQueue(dependencies);
}

export function continueDefaultGraphQueue(dependencies: DefaultGraphQueueDependencies): void {
  if (activeKey !== null || dependencies.anyBusy()) return;
  while (queue.length) {
    const next = queue.shift();
    if (!next) return;
    const visualizer = visualizerForOrd(next.ord);
    if (!visualizer) {
      retryDefaultGraph(next, dependencies);
      return;
    }
    const controls = controlsForOrd(next.ord);
    if (!controls) {
      retryDefaultGraph(next, dependencies);
      return;
    }
    const mountedSource = controls.dataset.aqeSourceFilename || next.sourceFilename;
    if (mountedSource !== next.sourceFilename) continue;
    if (
      visualizer.dataset.hasTrack === "true"
      && visualizer.dataset.sourceFilename === next.sourceFilename
    ) {
      continue;
    }
    activeKey = next.key;
    activeOrd = next.ord;
    dependencies.requestDefaultGraph({
      ord: next.ord,
      sourceFilename: next.sourceFilename,
    });
    return;
  }
}

export function finishDefaultGraphRequest(
  ord: number,
  dependencies: DefaultGraphQueueDependencies,
): void {
  if (activeOrd !== ord) return;
  activeKey = null;
  activeOrd = null;
  queueMicrotask(() => continueDefaultGraphQueue(dependencies));
}

function defaultGraphKey(target: DefaultGraphTarget): string {
  return `${target.ord}\u0000${target.sourceFilename}`;
}

function retryDefaultGraph(
  target: QueuedDefaultGraph,
  dependencies: DefaultGraphQueueDependencies,
): void {
  queue.unshift(target);
  if (retryScheduled) return;
  retryScheduled = true;
  window.setTimeout(() => {
    retryScheduled = false;
    continueDefaultGraphQueue(dependencies);
  }, 0);
}
