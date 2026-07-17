import { reduceChorusingProgram } from "./chorusing.js";
import type { PracticeFact, PracticeProgramState, ProgramTransition } from "./model.js";
import { reduceOnceProgram } from "./once.js";
import { reduceRecordOnceProgram } from "./record-once.js";
import { reduceRepeatProgram } from "./repeat.js";

export function reducePracticeProgram(
  state: PracticeProgramState,
  fact: PracticeFact,
): ProgramTransition<PracticeProgramState> {
  switch (state.kind) {
    case "once": return reduceOnceProgram(state, fact);
    case "repeat": return reduceRepeatProgram(state, fact);
    case "chorusing": return reduceChorusingProgram(state, fact);
    case "record_once": return reduceRecordOnceProgram(state, fact);
    default: return exhaustive(state);
  }
}

function exhaustive(value: never): never {
  throw new Error(`Unhandled practice program: ${JSON.stringify(value)}`);
}
