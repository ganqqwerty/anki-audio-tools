import {
  allReviewerPanelTriggers,
  controlsForRawOrd,
  reviewerPanelTargetForTrigger,
} from "./dom-selectors.js";

export function installReviewerPanelTriggers(scan: () => void): void {
  allReviewerPanelTriggers().forEach((trigger) => {
    if (trigger.dataset.aqeTriggerInstalled === "true") return;
    trigger.dataset.aqeTriggerInstalled = "true";
    trigger.addEventListener("click", () => {
      const target = reviewerPanelTargetForTrigger(trigger);
      if (target) {
        target.dataset.aqePanelOpen = "true";
      }
      trigger.hidden = true;
      scan();
      focusControls(trigger.dataset.fieldOrd);
    });
  });
}

export function reviewTargetIsOpen(node: HTMLElement): boolean {
  return node.dataset.aqePanelTriggerTarget !== "true" || node.dataset.aqePanelOpen === "true";
}

function focusControls(rawOrd: string | undefined): void {
  if (!rawOrd || !/^\d+$/.test(rawOrd)) return;
  window.setTimeout(() => {
    const controls = controlsForRawOrd(rawOrd);
    controls?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
    controls?.querySelector<HTMLButtonElement>("button")?.focus();
  }, 0);
}
