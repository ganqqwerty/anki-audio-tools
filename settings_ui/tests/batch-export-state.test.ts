import { describe, expect, it } from "vitest";

import {
  audioExportStartRequest,
  canStartAudioExport,
  initialAudioExportFormState,
  selectedFieldCount,
  setAudioExportFieldSelected,
} from "../src/batch/export-state.js";
import {
  AudioExportMode,
  BatchSurface,
  Direction,
} from "../src/lib/types.js";
import type { AudioExportInitialState } from "../src/lib/types.js";

function exportState(): AudioExportInitialState {
  return {
    surface: BatchSurface.AudioExport,
    note_count: 3,
    field_groups: [
      { notetype_name: "Basic", fields: ["Audio", "Image"] },
      { notetype_name: "Cloze", fields: ["SentenceAudio", "Hint"] },
    ],
    default_field_selections: [
      { notetype_name: "Basic", fields: ["Audio"] },
      { notetype_name: "Cloze", fields: ["SentenceAudio"] },
    ],
    defaults: {
      mode: AudioExportMode.Zip,
      silence_between_clips_seconds: 1.5,
    },
    locale: "en",
    direction: Direction.LTR,
    messages: {},
  };
}

describe("audio export state", () => {
  it("initializes from default field selections", () => {
    const form = initialAudioExportFormState(exportState());

    expect(form.mode).toBe(AudioExportMode.Zip);
    expect(form.destinationPath).toBe("");
    expect(form.silenceBetweenClipsSeconds).toBe(1.5);
    expect(form.selectedFields.Basic).toEqual(new Set(["Audio"]));
    expect(form.selectedFields.Cloze).toEqual(new Set(["SentenceAudio"]));
    expect(Object.keys(form.selectedFields)).toEqual(["Basic", "Cloze"]);
    expect(selectedFieldCount(form)).toBe(2);
  });

  it("requires destination and at least one field", () => {
    const form = initialAudioExportFormState(exportState());

    expect(canStartAudioExport(form)).toBe(false);
    form.destinationPath = "  /tmp/cards.zip  ";
    expect(canStartAudioExport(form)).toBe(true);

    setAudioExportFieldSelected(form, "Basic", "Audio", false);
    setAudioExportFieldSelected(form, "Cloze", "SentenceAudio", false);
    expect(canStartAudioExport(form)).toBe(false);
  });

  it("builds generated bridge payload with selected fields and clamped silence", () => {
    const form = initialAudioExportFormState(exportState());
    form.mode = AudioExportMode.CombinedMp3;
    form.destinationPath = " /tmp/cards.mp3 ";
    form.silenceBetweenClipsSeconds = 45;
    setAudioExportFieldSelected(form, "Basic", "Image", true);
    setAudioExportFieldSelected(form, "Cloze", "SentenceAudio", false);

    expect(audioExportStartRequest(form)).toEqual({
      mode: AudioExportMode.CombinedMp3,
      destination_path: "/tmp/cards.mp3",
      field_selections: [
        { notetype_name: "Basic", fields: ["Audio", "Image"] },
      ],
      silence_between_clips_seconds: 10,
    });
  });
});
