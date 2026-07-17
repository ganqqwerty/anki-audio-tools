import type { TransportFailureIdentity } from "./transport-public-types.js";

export interface ConvertToMp3RecoveryProposal {
  fieldOrd: number;
  kind: "convert_to_mp3";
  sourceFilename: string;
}

export interface ConvertToMp3RecoveryAction extends ConvertToMp3RecoveryProposal {
  failureIdentity: TransportFailureIdentity;
}

export type PlaybackRecoveryProposal = ConvertToMp3RecoveryProposal;
export type PlaybackRecoveryAction = ConvertToMp3RecoveryAction;
