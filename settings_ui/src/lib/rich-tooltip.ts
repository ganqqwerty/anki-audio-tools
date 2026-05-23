export const TOOLTIP_CONTENT_ATTRIBUTE = "data-aqe-tooltip-content";

export function setTooltipContent(target: HTMLElement | null, content: string): void {
  if (!target) return;
  const normalized = content.trim();
  if (normalized) {
    target.setAttribute(TOOLTIP_CONTENT_ATTRIBUTE, normalized);
  } else {
    target.removeAttribute(TOOLTIP_CONTENT_ATTRIBUTE);
  }
}

export function setButtonTooltipContent(button: HTMLButtonElement | null, content: string): void {
  if (!button) return;
  setTooltipContent(button.closest<HTMLElement>(".aqe-tooltip-target") ?? button, content);
  button.setAttribute("aria-label", content);
}
