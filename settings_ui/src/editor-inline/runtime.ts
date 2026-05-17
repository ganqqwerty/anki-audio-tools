import {
  prepareForNewNote,
  requestPendingGraphRedraw,
} from "./actions.js";
import {
  disposeAllControllers,
  mountController,
} from "./field-controller.js";
import { logger } from "./logger.js";
import type { EditorRuntimeConfig, FieldTarget } from "./types.js";
import { installEditorWindowContract } from "./window-contract.js";

const soundPattern = /\[sound:([^\]]+)\]/i;
const supportedPattern = /\.(mp3|wav|ogg)$/i;
let scheduledScanTimers: number[] = [];

export function initializeEditorRuntime(config: EditorRuntimeConfig = window.__AQE_EDITOR_CONFIG__ ?? { audioFieldIndices: [] }): void {
  disposeEditorRuntime();
  window.__AQE_EDITOR_CONFIG__ = config;
  installEditorWindowContract();
  prepareForNewNote();
  window.__aqeEditorDispose = disposeEditorRuntime;
  logger.info("editor runtime initialized", { audioFieldIndices: config.audioFieldIndices });
  const scanWithConfig = (): void => scan(config);
  window.__aqeScan = scanWithConfig;
  scheduleScan(scanWithConfig, 0);
  scheduleScan(scanWithConfig, 250);
  scheduleScan(scanWithConfig, 1000);
}

export function disposeEditorRuntime(): void {
  scheduledScanTimers.forEach((timer) => window.clearTimeout(timer));
  scheduledScanTimers = [];
  disposeAllControllers();
}

export function scan(config: EditorRuntimeConfig = window.__AQE_EDITOR_CONFIG__ ?? { audioFieldIndices: [] }): void {
  if (config.audioFieldIndices.length) {
    const explicitTargets = explicitFieldTargets(config.audioFieldIndices);
    explicitTargets.forEach((target) => mountNear(target));
    logger.debug("scan mounted explicit fields", { count: explicitTargets.length });
    requestPendingGraphRedraw();
    return;
  }
  let count = 0;
  fieldNodes().forEach((node, fallback) => {
    const sourceFilename = audioSourceForNode(node);
    if (!sourceFilename) return;
    mountNear({
      node,
      ord: fieldIndex(node, fallback),
      sourceFilename,
    });
    count += 1;
  });
  logger.debug("scan mounted detected fields", { count });
  requestPendingGraphRedraw();
}

export function fieldNodes(): HTMLElement[] {
  const candidates = Array.from(document.querySelectorAll<HTMLElement>('[contenteditable="true"], .field, [data-field-ord]'));
  const seen = new Set<HTMLElement>();
  return candidates.filter((node) => {
    if (seen.has(node)) return false;
    seen.add(node);
    return !!(node.textContent || node.innerHTML);
  });
}

export function explicitFieldTargets(audioFieldIndices: readonly number[]): FieldTarget[] {
  return audioFieldIndices
    .map((ord): FieldTarget | null => {
      const container = document.querySelector<HTMLElement>(`.field-container[data-index="${ord}"]`);
      if (!container) return null;
      const node = container.querySelector<HTMLElement>('[contenteditable="true"]') || container;
      const sourceFilename = audioSourceForNode(node) || audioSourceForNode(container);
      return {
        ord,
        node,
        sourceFilename,
      };
    })
    .filter((target): target is FieldTarget => target !== null);
}

export function fieldIndex(node: HTMLElement, fallback: number): number {
  const attrs = ["data-field-ord", "data-ord", "data-index"] as const;
  for (const attr of attrs) {
    const raw = node.getAttribute(attr);
    if (raw !== null && /^\d+$/.test(raw)) return Number(raw);
  }
  const idMatch = /(\d+)/.exec(String(node.id || ""));
  return idMatch ? Number(idMatch[1]) : fallback;
}

export function audioSourceForNode(node: HTMLElement): string {
  const html = node.innerHTML || node.textContent || "";
  const match = soundPattern.exec(html);
  const filename = match?.[1];
  return filename && supportedPattern.test(filename) ? filename : "";
}

export function mountNear(target: FieldTarget): void {
  mountController(target);
}

function scheduleScan(callback: () => void, delayMs: number): void {
  const timer = window.setTimeout(() => {
    scheduledScanTimers = scheduledScanTimers.filter((scheduled) => scheduled !== timer);
    callback();
  }, delayMs);
  scheduledScanTimers.push(timer);
}
