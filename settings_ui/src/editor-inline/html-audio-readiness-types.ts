export type HtmlAudioReadinessState = "failed" | "loading_metadata" | "missing" | "ready" | "source_missing";

export type HtmlAudioReadinessReason =
  | "audio_element_missing"
  | "audio_error"
  | "audio_load_failed"
  | "audio_metadata_loading"
  | "audio_pause_failed"
  | "audio_play_rejected"
  | "audio_ready"
  | "audio_seek_failed"
  | "audio_src_missing"
  | "metadata_timeout";

export interface HtmlAudioReadiness {
  failed: boolean;
  ready: boolean;
  reason: HtmlAudioReadinessReason;
  state: HtmlAudioReadinessState;
  transient: boolean;
}

export interface HtmlAudioReadinessInput {
  available: boolean;
  failureReason?: HtmlAudioReadinessReason | "";
  hasSrc: boolean;
  present: boolean;
  readyState: number | null;
}
