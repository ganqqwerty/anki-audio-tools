import type { PlaybackRecoveryAction } from "./playback-recovery-types.js";
import type {
  HtmlAudioSessionEvent,
  HtmlAudioSessionState,
} from "./html-audio-session-types.js";
import type { TransportFailureIdentity } from "./transport/index.js";

interface HtmlAudioSessionRecoveryDependencies {
  acceptsFailure: (ord: number, identity: TransportFailureIdentity) => boolean;
  claimFailure: (ord: number, identity: TransportFailureIdentity) => boolean;
  dispatchFailureFact: (
    ord: number,
    identity: TransportFailureIdentity,
    event: HtmlAudioSessionEvent,
  ) => void;
  readState: (ord: number) => HtmlAudioSessionState;
}

/** Claims only the recovery proposal owned by the current failed source. */
export class HtmlAudioSessionRecovery {
  constructor(private readonly dependencies: HtmlAudioSessionRecoveryDependencies) {}

  claim(action: PlaybackRecoveryAction): boolean {
    const state = this.dependencies.readState(action.fieldOrd);
    if (
      state.kind !== "failed"
      || state.recovery !== "available"
      || state.source?.kind !== "source"
      || state.source.sourceFilename !== action.sourceFilename
      || !this.dependencies.acceptsFailure(action.fieldOrd, action.failureIdentity)
    ) {
      return false;
    }
    this.dependencies.dispatchFailureFact(action.fieldOrd, action.failureIdentity, {
      type: "RecoveryClaimed",
    });
    return this.dependencies.claimFailure(action.fieldOrd, action.failureIdentity);
  }
}
