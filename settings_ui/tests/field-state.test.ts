import { describe, expect, it } from "vitest";

import {
  draftSelectionCommitted,
  effectivePlaybackRegion,
  graphRendered,
  graphRequested,
  initialFieldState,
  playbackPaused,
  playbackStarted,
  playbackStopped,
  repeatToggled,
  resetForNewNote,
  selectionCleared,
  selectionCommitted,
  selectionDraftChanged,
} from "../src/editor-inline/field-state.js";

describe("editor field state", () => {
  it("initializes repeat from runtime config", () => {
    expect(initialFieldState({ ord: 2, repeatByDefault: true })).toMatchObject({
      ord: 2,
      playback: {
        repeat: true,
        state: "stopped",
      },
    });
  });

  it("resets graph, cursor, selection, and playback when graph analysis starts", () => {
    const selected = selectionCommitted(
      graphRendered(initialFieldState({ ord: 0 }), {
        analyzerName: "praat",
        cursorMs: 250,
        durationMs: 1000,
        sourceFilename: "clip.mp3",
      }),
      200,
      900,
    );

    expect(graphRequested(selected)).toMatchObject({
      cursor: { anchorMs: 0, ms: 0, progressMs: 0 },
      graph: { active: true, busy: true, durationMs: 0, hasTrack: false },
      playback: { engine: "", regionMode: "full", state: "stopped" },
      selection: { active: false, draftActive: false },
      sourceFilename: "",
    });
  });

  it("renders graph payload into typed state and clears stale selection", () => {
    const state = graphRendered(initialFieldState({ ord: 0 }), {
      analyzerName: "praat",
      cursorMs: 1200,
      durationMs: 1000,
      sourceFilename: "nested/clip.mp3",
    });

    expect(state).toMatchObject({
      cursor: { anchorMs: 1000, ms: 1000, progressMs: 1000 },
      graph: { analyzerName: "praat", busy: false, durationMs: 1000, hasTrack: true },
      playback: { endMs: 1000, regionMode: "full", startMs: 0 },
      sourceFilename: "nested/clip.mp3",
    });
  });

  it("normalizes committed and draft selections", () => {
    const state = graphRendered(initialFieldState({ ord: 0 }), {
      analyzerName: "praat",
      cursorMs: 0,
      durationMs: 1000,
      sourceFilename: "clip.mp3",
    });
    const selected = selectionCommitted(state, 900, 200);

    expect(selected).toMatchObject({
      cursor: { ms: 200 },
      playback: { startMs: 200, endMs: 900, regionMode: "selection" },
      selection: { active: true, startMs: 200, endMs: 900 },
    });

    const draft = selectionDraftChanged(selected, 800, 400);
    expect(draft.selection).toMatchObject({ active: true, draftActive: true, draftStartMs: 400, draftEndMs: 800 });
    expect(draftSelectionCommitted(draft).selection).toMatchObject({ active: true, startMs: 400, endMs: 800 });
    expect(selectionCleared(selected)).toMatchObject({
      playback: { startMs: 0, endMs: 1000, regionMode: "full" },
      selection: { active: false },
    });
  });

  it("models repeat and playback transitions without DOM", () => {
    const state = graphRendered(initialFieldState({ ord: 0 }), {
      analyzerName: "praat",
      cursorMs: 0,
      durationMs: 1000,
      sourceFilename: "clip.mp3",
    });
    const playing = playbackStarted(repeatToggled(state, true), 500, { clockMode: "audio", engine: "html" });

    expect(effectivePlaybackRegion(playing)).toEqual({ startMs: 0, endMs: 1000, mode: "full" });
    expect(playing).toMatchObject({
      cursor: { ms: 500 },
      playback: { clockMode: "audio", engine: "html", repeat: true, state: "playing" },
    });
    expect(playbackPaused(playing, 650)).toMatchObject({ cursor: { ms: 650 }, playback: { state: "paused" } });
    expect(playbackStopped(playing)).toMatchObject({ playback: { engine: "", state: "stopped" } });
  });

  it("resets for a new note while preserving the requested repeat default", () => {
    const state = graphRendered(initialFieldState({ ord: 5, repeatByDefault: true }), {
      analyzerName: "praat",
      cursorMs: 500,
      durationMs: 1000,
      sourceFilename: "clip.mp3",
    });

    expect(resetForNewNote(state, false)).toMatchObject({
      ord: 5,
      graph: { active: false, durationMs: 0 },
      playback: { repeat: false, state: "stopped" },
    });
  });
});
