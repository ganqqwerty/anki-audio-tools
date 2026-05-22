import type { SplitButtonDefaults } from "./types.js";

export interface SplitDefaultSaveRequest {
  defaults: Partial<SplitButtonDefaults> & {
    repeatPlaybackByDefault?: boolean;
  };
  fieldOrd: number;
}
