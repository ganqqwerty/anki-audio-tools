import { describe, expect, it } from "vitest";

import { buildEditorToolbarRenderItems } from "../src/editor-inline/editor-toolbar-render-items.js";
import { toolbarButtons } from "../src/lib/editor-toolbar-buttons.js";
import { visibleToolbarButtons } from "../src/lib/editor-toolbar-visibility.js";

describe("editor toolbar render items", () => {
  it("renders shared atomic panels as toolbar panel items", () => {
    const items = buildEditorToolbarRenderItems(toolbarButtons());
    const panels = items.filter((item) => item.kind === "toolbar-panel");

    expect(panels.map((item) => ({
      commands: item.buttons.map((button) => button.command),
      description: item.description,
      label: item.label,
      slug: item.definition.slug,
    }))).toEqual([
      {
        commands: [
          "aqe:chorusing-practice",
          "aqe:chorusing-next",
          "aqe:chorusing-previous",
        ],
        description: "Practice the audio from the end, word by word, until you can repeat the whole sentence.",
        label: "Chorusing",
        slug: "chorusing",
      },
      {
        commands: [
          "aqe:record-voice",
          "aqe:play-recording",
          "aqe:share-recording",
          "aqe:show-recording-file",
        ],
        description: "Record your voice for the current graph, then play, share, or show your latest recording.",
        label: "Record / Play yours",
        slug: "record-play-yours",
      },
    ]);
  });

  it("uses a play icon for the Play yours recording command", () => {
    const playRecording = toolbarButtons().find((button) => button.command === "aqe:play-recording");

    expect(playRecording).toMatchObject({
      activeIcon: "pause",
      icon: "play",
    });
  });

  it("keeps speed and volume as split run groups, not toolbar panels", () => {
    const items = buildEditorToolbarRenderItems(toolbarButtons());

    expect(items.filter((item) => item.kind === "split-run-group").map((item) => item.menuSlug)).toEqual([
      "speed",
      "volume",
    ]);
  });

  it("keeps partially visible chorusing buttons inside the toolbar panel", () => {
    const items = buildEditorToolbarRenderItems(
      visibleToolbarButtons(toolbarButtons(), [
        "aqe:play",
        "aqe:chorusing-practice",
        "aqe:chorusing-next",
        "aqe:settings",
      ]),
    );
    const panels = items.filter((item) => item.kind === "toolbar-panel");

    expect(panels).toEqual([
      expect.objectContaining({
        buttons: expect.arrayContaining([
          expect.objectContaining({ command: "aqe:chorusing-practice" }),
          expect.objectContaining({ command: "aqe:chorusing-next" }),
        ]),
        definition: expect.objectContaining({ slug: "chorusing" }),
      }),
    ]);
    expect(panels[0]?.buttons.map((button) => button.command)).toEqual([
      "aqe:chorusing-practice",
      "aqe:chorusing-next",
    ]);
  });
});
