import { mount, unmount } from "svelte";

import EditorControls from "./EditorControls.svelte";
import {
  getCursorIntent,
  getCursorMs,
  getPlaybackRequest,
  graphStateForTest,
  installAudioPlaybackTestDriver,
  popEditorFrontendLog,
  prepareForNewNote,
  resetGraphAfterEdit,
  setControlsBusy,
  setCursorByClientXForTest,
  setCursorForTest,
  setPlaybackState,
  setStatus,
  setVisualizer,
  setVisualizerStatusFromPython,
  stopEditorPlayback,
  visualizerForOrd,
} from "./actions.js";
import { logger } from "./logger.js";
import type { EditorRuntimeConfig, FieldTarget, MountedField } from "./types.js";

const soundPattern = /\[sound:([^\]]+)\]/i;
const supportedPattern = /\.(mp3|wav|ogg)$/i;
const mountedFields = new Map<number, MountedField>();

export function initializeEditorRuntime(config: EditorRuntimeConfig = window.__AQE_EDITOR_CONFIG__ ?? { audioFieldIndices: [] }): void {
  disposeEditorRuntime();
  window.__AQE_EDITOR_CONFIG__ = config;
  installWindowContract();
  prepareForNewNote();
  window.__aqeEditorDispose = disposeEditorRuntime;
  logger.info("editor runtime initialized", { audioFieldIndices: config.audioFieldIndices });
  const scanWithConfig = (): void => scan(config);
  window.__aqeScan = scanWithConfig;
  window.setTimeout(scanWithConfig, 0);
  window.setTimeout(scanWithConfig, 250);
  window.setTimeout(scanWithConfig, 1000);
}

export function disposeEditorRuntime(): void {
  for (const mounted of mountedFields.values()) {
    void unmount(mounted.component);
    mounted.host.remove();
  }
  mountedFields.clear();
}

export function scan(config: EditorRuntimeConfig = window.__AQE_EDITOR_CONFIG__ ?? { audioFieldIndices: [] }): void {
  if (config.audioFieldIndices.length) {
    const explicitTargets = explicitFieldTargets(config.audioFieldIndices);
    explicitTargets.forEach((target) => mountNear(target));
    logger.debug("scan mounted explicit fields", { count: explicitTargets.length });
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
  const existing = mountedFields.get(target.ord);
  if (existing && document.body.contains(existing.host)) {
    if (!target.sourceFilename || existing.sourceFilename === target.sourceFilename) {
      return;
    }
    const visualizer = visualizerForOrd(target.ord);
    if (visualizer?.dataset.graphBusy === "true" || visualizer?.dataset.hasTrack === "true") {
      const renderedSource = visualizer.dataset.sourceFilename || target.sourceFilename;
      existing.sourceFilename = renderedSource;
      const controls = document.querySelector<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${target.ord}"]`);
      if (controls) controls.dataset.aqeSourceFilename = renderedSource;
      return;
    }
  }
  disposeField(target.ord);
  const parent = target.node.closest(".field-container")
    || target.node.closest(".field")
    || target.node.parentElement
    || target.node;
  const host = document.createElement("div");
  host.className = "aqe-mount-host";
  if (parent.parentElement) {
    parent.after(host);
  } else {
    target.node.after(host);
  }
  const component = mount(EditorControls, {
    target: host,
    props: { target },
  }) as Record<string, unknown>;
  mountedFields.set(target.ord, {
    component,
    host,
    ord: target.ord,
    sourceFilename: target.sourceFilename,
  });
}

function disposeField(ord: number): void {
  const mounted = mountedFields.get(ord);
  if (mounted) {
    void unmount(mounted.component);
    mounted.host.remove();
    mountedFields.delete(ord);
  }
  document.querySelectorAll<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${ord}"]`).forEach((node) => node.remove());
}

function installWindowContract(): void {
  window.__aqeSetBusy = setControlsBusy;
  window.__aqeSetStatus = setStatus;
  window.__aqeSetVisualizer = setVisualizer;
  window.__aqeSetVisualizerStatus = setVisualizerStatusFromPython;
  window.__aqeResetGraphAfterEdit = resetGraphAfterEdit;
  window.__aqeSetPlaybackState = setPlaybackState;
  window.__aqeGetPlaybackRequest = getPlaybackRequest;
  window.__aqeStopEditorPlayback = stopEditorPlayback;
  window.__aqeInstallAudioPlaybackTestDriverForTest = installAudioPlaybackTestDriver;
  window.__aqeGetCursorMs = getCursorMs;
  window.__aqeGetCursorIntent = getCursorIntent;
  window.__aqeSetCursorForTest = setCursorForTest;
  window.__aqeSetCursorByClientXForTest = setCursorByClientXForTest;
  window.__aqeGraphStateForTest = graphStateForTest;
  window.__aqePrepareForNewNote = prepareForNewNote;
  window.__aqePopFrontendLog = popEditorFrontendLog;
}
