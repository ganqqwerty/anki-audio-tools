import type { AudioSourceMetadataSummary } from "../lib/size-reduction-parameters.js";

export interface SourceMetadataRequest {
  requestId: string;
  fieldOrd: number;
  sourceFilename: string;
}

export interface SourceMetadataResponse {
  requestId: string;
  ok: boolean;
  metadata?: AudioSourceMetadataSummary;
  error?: string;
}
