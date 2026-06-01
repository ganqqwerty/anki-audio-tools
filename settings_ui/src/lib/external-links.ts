import { sendBridgeEnvelope } from "./bridge.js";

export function openExternalLink(event: MouseEvent, url: string): void {
  event.preventDefault();
  event.stopPropagation();
  sendBridgeEnvelope("webview.open_url", { url });
}
