export interface ConvertToMp3RecoveryAction {
  fieldOrd: number;
  kind: "convert_to_mp3";
  sourceFilename: string;
}

export type PlaybackRecoveryAction = ConvertToMp3RecoveryAction;

export const PLAYBACK_RECOVERY_REQUESTED_EVENT = "aqe-playback-recovery-requested";

export interface PlaybackRecoveryRequestedDetail {
  node: HTMLButtonElement;
  ord: number;
  surface: "status" | "warning";
}
