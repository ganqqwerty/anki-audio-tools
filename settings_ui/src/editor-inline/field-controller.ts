import { mount, unmount } from "svelte";

import EditorControls from "./EditorControls.svelte";
import { visualizerForOrd } from "./dom-selectors.js";
import type { FieldTarget } from "./types.js";

export interface FieldController {
  component: Record<string, unknown>;
  host: HTMLElement;
  ord: number;
  sourceFilename: string;
}

const controllers = new Map<number, FieldController>();

export function getController(ord: number): FieldController | null {
  return controllers.get(ord) ?? null;
}

export function mountedControllerCount(): number {
  return controllers.size;
}

export function mountController(target: FieldTarget): FieldController | null {
  const existing = controllers.get(target.ord);
  if (existing) {
    if (!document.body.contains(existing.host)) {
      insertHostNearTarget(target, existing.host);
    }
    removeDuplicateControls(target.ord, existing.host);
    if (!target.sourceFilename || existing.sourceFilename === target.sourceFilename) {
      return existing;
    }
    const visualizer = visualizerForOrd(target.ord);
    if (visualizer?.dataset.graphBusy === "true" || visualizer?.dataset.hasTrack === "true") {
      const renderedSource = visualizer.dataset.sourceFilename || target.sourceFilename;
      existing.sourceFilename = renderedSource;
      const controls = document.querySelector<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${target.ord}"]`);
      if (controls) controls.dataset.aqeSourceFilename = renderedSource;
      removeDuplicateControls(target.ord, existing.host);
      return existing;
    }
  }

  disposeController(target.ord);
  const host = document.createElement("div");
  host.className = "aqe-mount-host";
  insertHostNearTarget(target, host);
  const component = mount(EditorControls, {
    target: host,
    props: { target },
  }) as Record<string, unknown>;
  const controller = {
    component,
    host,
    ord: target.ord,
    sourceFilename: target.sourceFilename,
  };
  controllers.set(target.ord, controller);
  removeDuplicateControls(target.ord, host);
  return controller;
}

export function disposeController(ord: number): void {
  const controller = controllers.get(ord);
  if (controller) {
    void unmount(controller.component);
    controller.host.remove();
    controllers.delete(ord);
  }
  document.querySelectorAll<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${ord}"]`).forEach((node) => node.remove());
}

export function disposeAllControllers(): void {
  for (const controller of controllers.values()) {
    void unmount(controller.component);
    controller.host.remove();
  }
  controllers.clear();
  removeOrphanedControls();
}

function insertHostNearTarget(target: FieldTarget, host: HTMLElement): void {
  const parent = target.node.closest(".field-container")
    || target.node.closest(".field")
    || target.node.parentElement
    || target.node;
  if (parent.parentElement) {
    parent.after(host);
  } else {
    target.node.after(host);
  }
}

function removeDuplicateControls(ord: number, keepHost: HTMLElement): void {
  document.querySelectorAll<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${ord}"]`).forEach((controls) => {
    if (!keepHost.contains(controls)) {
      controls.remove();
    }
  });
  document.querySelectorAll<HTMLElement>(".aqe-mount-host").forEach((host) => {
    if (host !== keepHost && !host.querySelector(".aqe-controls")) {
      host.remove();
    }
  });
}

function removeOrphanedControls(): void {
  document.querySelectorAll<HTMLElement>(".aqe-mount-host").forEach((host) => host.remove());
  document.querySelectorAll<HTMLElement>(".aqe-controls").forEach((controls) => controls.remove());
}
