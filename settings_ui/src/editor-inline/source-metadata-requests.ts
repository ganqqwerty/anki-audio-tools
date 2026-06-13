import type { AudioSourceMetadataSummary } from "../lib/size-reduction-parameters.js";
import { sendSourceMetadataRequest } from "./bridge.js";
import type { SourceMetadataResponse } from "./source-metadata-types.js";

const pending = new Map<
  string,
  {
    reject: (error: Error) => void;
    resolve: (metadata: AudioSourceMetadataSummary) => void;
  }
>();

let counter = 0;

export function requestSourceMetadata(
  fieldOrd: number,
  sourceFilename: string,
): Promise<AudioSourceMetadataSummary> {
  counter += 1;
  const requestId = `source_${counter}_${Date.now()}`;
  const promise = new Promise<AudioSourceMetadataSummary>((resolve, reject) => {
    pending.set(requestId, { resolve, reject });
  });
  sendSourceMetadataRequest({ requestId, fieldOrd, sourceFilename });
  return promise;
}

export function receiveSourceMetadataResponse(response: SourceMetadataResponse): void {
  const callbacks = pending.get(response.requestId);
  if (!callbacks) return;
  pending.delete(response.requestId);
  if (response.ok && response.metadata) {
    callbacks.resolve(response.metadata);
    return;
  }
  callbacks.reject(new Error(response.error || "Could not inspect source info."));
}

export function clearSourceMetadataRequests(): void {
  pending.clear();
  counter = 0;
}
