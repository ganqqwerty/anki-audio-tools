import { sendExternalLinkRequest } from "./bridge.js";

export function openEditorExternalLink(event: MouseEvent, url: string): void {
  event.preventDefault();
  event.stopPropagation();
  sendExternalLinkRequest(url);
}
