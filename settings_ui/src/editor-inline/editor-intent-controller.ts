import { Outcome, type EditorIntentReceipt } from "../lib/generated/contracts.js";
import { sendBridgeEnvelope } from "../lib/bridge-transport.js";
import { visualizerForOrd } from "./dom-selectors.js";
import { editorRuntimeConfig } from "./editor-runtime-config.js";
import { startEditorPlaybackPractice } from "./editor-practice-controller.js";
import type { HtmlAudioStartRequest } from "./html-audio-session-types.js";
import { logger } from "./logger.js";

interface AcceptedEditorIntent {
  deliveryId: string;
  editorSessionId: number;
  ord: number;
  request: HtmlAudioStartRequest;
  sourceFilename: string;
}

class EditorIntentController {
  private consumedDeliveryId: string | null = null;

  accept(candidate: AcceptedEditorIntent): boolean {
    const pending = editorRuntimeConfig().pendingEditorIntent;
    if (!pendingEditorIntentMatches(pending, candidate)) {
      logger.debug("editor.intent_stale", { deliveryId: candidate.deliveryId, ord: candidate.ord });
      return false;
    }
    if (this.consumedDeliveryId === candidate.deliveryId) return false;
    const visualizer = visualizerForOrd(candidate.ord);
    if (!visualizer) {
      sendReceipt(candidate.deliveryId, candidate.editorSessionId, Outcome.Failed);
      return false;
    }
    this.consumedDeliveryId = candidate.deliveryId;
    startEditorPlaybackPractice(visualizer, candidate.request);
    sendReceipt(candidate.deliveryId, candidate.editorSessionId, Outcome.AutoplayAccepted);
    logger.info("editor.intent_autoplay_accepted", {
      deliveryId: candidate.deliveryId,
      editorSessionId: candidate.editorSessionId,
      ord: candidate.ord,
    });
    return true;
  }

  failForOrd(ord: number): void {
    const pending = editorRuntimeConfig().pendingEditorIntent;
    if (
      !pending
      || pending.target.fieldOrd !== ord
      || this.consumedDeliveryId === pending.deliveryId
    ) return;
    this.consumedDeliveryId = pending.deliveryId;
    sendReceipt(pending.deliveryId, pending.target.editorSessionId, Outcome.Failed);
  }

  dispose(): void {
    this.consumedDeliveryId = null;
  }
}

let activeController: EditorIntentController | null = null;

export function initializeEditorIntentController(): void {
  activeController?.dispose();
  activeController = new EditorIntentController();
}

function controller(): EditorIntentController {
  activeController ??= new EditorIntentController();
  return activeController;
}

export function acceptPendingEditorIntent(candidate: AcceptedEditorIntent): boolean {
  return controller().accept(candidate);
}

export function failPendingEditorIntentForOrd(ord: number): void {
  controller().failForOrd(ord);
}

export function disposeEditorIntentController(): void {
  activeController?.dispose();
  activeController = null;
}

function pendingEditorIntentMatches(
  pending: ReturnType<typeof editorRuntimeConfig>["pendingEditorIntent"],
  candidate: AcceptedEditorIntent,
): boolean {
  return Boolean(
    pending
    && pending.schemaVersion === 1
    && pending.expiresAtEpochMs > Date.now()
    && pending.deliveryId === candidate.deliveryId
    && pending.target.editorSessionId === candidate.editorSessionId
    && pending.target.fieldOrd === candidate.ord
    && pending.target.sourceFilename === candidate.sourceFilename
  );
}

function sendReceipt(deliveryId: string, editorSessionId: number, outcome: Outcome): void {
  const receipt: EditorIntentReceipt = {
    deliveryId,
    editorSessionId,
    outcome,
    schemaVersion: 1,
  };
  sendBridgeEnvelope("editor.intent-receipt", receipt);
}
