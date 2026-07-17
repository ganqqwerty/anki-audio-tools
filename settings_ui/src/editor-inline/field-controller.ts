import { mount, unmount } from "svelte";

import {
  consumeInitialStatusForOrd,
  applyInitialHistoryAvailabilityForOrd,
  setStatusForOrd,
  type InitialEditorStatus,
} from "./control-actions.js";
import EditorControls from "./EditorControls.svelte";
import { visualizerForOrd } from "./dom-selectors.js";
import { initFieldState, readFieldState, removeFieldState } from "./field-state-store.js";
import { initialFieldState } from "./field-state.js";
import {
  dispatchHtmlAudioSessionEvent,
  mountHtmlAudioTransportField,
  unmountHtmlAudioTransportField,
} from "./html-audio-session-controller.js";
import type { FieldTarget } from "./types.js";
import { postEditPlaybackIntentForOrd } from "./post-edit-playback.js";

export interface FieldController {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Svelte mount()/unmount() use Record<string, any>
  component: Record<string, any>;
  host: HTMLElement;
  ord: number;
  sourceFilename: string;
  target: FieldTarget;
}

const controllers = new Map<number, FieldController>();

export function getController(ord: number): FieldController | null {
  return controllers.get(ord) ?? null;
}

export function mountedControllerCount(): number {
  return controllers.size;
}

export function mountController(target: FieldTarget): FieldController | null {
  const initialStatus = consumeInitialStatusForOrd(target.ord);
  const existing = controllers.get(target.ord);
  if (existing) {
    if (!document.body.contains(existing.host)) {
      insertHostNearTarget(target, existing.host);
    }
    removeDuplicateControls(target.ord, existing.host);
    if (!target.sourceFilename || existing.sourceFilename === target.sourceFilename) {
      applyInitialStatus(target.ord, initialStatus);
      return existing;
    }
    const visualizer = visualizerForOrd(target.ord);
    if (visualizer) {
      const s = readFieldState(target.ord);
      if (s.graph.busy || s.graph.hasTrack) {
        existing.target.sourceFilename = target.sourceFilename;
        existing.sourceFilename = target.sourceFilename;
        dispatchHtmlAudioSessionEvent(target.ord, {
          cursorMs: s.cursor.ms,
          source: { kind: "source", sourceFilename: target.sourceFilename },
          type: "SourceConfigured",
        });
        removeDuplicateControls(target.ord, existing.host);
        applyInitialStatus(target.ord, initialStatus);
        return existing;
      }
    }
  }

  disposeController(target.ord);
  const host = document.createElement("div");
  host.className = "aqe-mount-host aqe-ui-root";
  host.dataset.aqeSurface = target.node.classList.contains("aqe-review-audio-target") ? "reviewer" : "editor";
  insertHostNearTarget(target, host);
  const component = mount(EditorControls, {
    target: host,
    props: { initialStatus, target },
  });
  applyInitialStatus(target.ord, initialStatus);
  applyInitialHistoryAvailabilityForOrd(target.ord);
  const controller = {
    component,
    host,
    ord: target.ord,
    sourceFilename: target.sourceFilename,
    target,
  };
  controllers.set(target.ord, controller);
  mountHtmlAudioTransportField(target.ord);
  const postEditPlayback = postEditPlaybackIntentForOrd(target.ord);
  initFieldState(target.ord, initialFieldState({
    ord: target.ord,
    ...(postEditPlayback ? { repeatByDefault: postEditPlayback.repeat } : {}),
    sourceFilename: target.sourceFilename,
  }));
  removeDuplicateControls(target.ord, host);
  return controller;
}

function applyInitialStatus(ord: number, initialStatus: InitialEditorStatus | null): void {
  if (!initialStatus) return;
  setStatusForOrd(ord, initialStatus.message, initialStatus.kind || "info", "", "edit");
}

export function disposeController(ord: number): void {
  const controller = controllers.get(ord);
  if (controller) {
    void unmount(controller.component);
    controller.host.remove();
    controllers.delete(ord);
  }
  unmountHtmlAudioTransportField(ord);
  removeFieldState(ord);
  document.querySelectorAll<HTMLElement>(`.aqe-controls[data-aqe-field-ord="${ord}"]`).forEach((node) => node.remove());
}

export function disposeAllControllers(): void {
  for (const controller of controllers.values()) {
    void unmount(controller.component);
    controller.host.remove();
    unmountHtmlAudioTransportField(controller.ord);
    removeFieldState(controller.ord);
  }
  controllers.clear();
  removeOrphanedControls();
}

function insertHostNearTarget(target: FieldTarget, host: HTMLElement): void {
  if (target.node.classList.contains("aqe-review-audio-target")) {
    target.node.append(host);
    return;
  }
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
