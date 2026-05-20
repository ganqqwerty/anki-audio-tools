export type GraphVoiceRange = "bass" | "low" | "general" | "high" | "child";
export type GraphRecordingCondition = "auto" | "very_noisy" | "noisy" | "normal" | "clean" | "studio";
export type GraphSmoothness = "raw" | "balanced" | "smooth" | "very_smooth";
export type GraphVoiceLock = "loose" | "balanced" | "stable";

export interface GraphSettings {
  connectShortDropoutsMs: number;
  recordingCondition: GraphRecordingCondition;
  smoothness: GraphSmoothness;
  voiceLock: GraphVoiceLock;
  voiceRange: GraphVoiceRange;
}
