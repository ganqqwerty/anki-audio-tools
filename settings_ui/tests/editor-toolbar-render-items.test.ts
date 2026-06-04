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
      label: item.label,
      slug: item.definition.slug,
    }))).toEqual([
      {
        commands: [
          "aqe:back-chain-practice",
          "aqe:back-chain-previous",
          "aqe:back-chain-next",
        ],
        label: "Back-chaining",
        slug: "back-chaining",
      },
      {
        commands: [
          "aqe:record-voice",
          "aqe:play-recording",
        ],
        label: "Record / Play yours",
        slug: "record-play-yours",
      },
    ]);
  });

  it("keeps speed and volume as split run groups, not toolbar panels", () => {
    const items = buildEditorToolbarRenderItems(toolbarButtons());

    expect(items.filter((item) => item.kind === "split-run-group").map((item) => item.menuSlug)).toEqual([
      "speed",
      "volume",
    ]);
  });

  it("keeps partially visible back-chaining buttons inside the toolbar panel", () => {
    const items = buildEditorToolbarRenderItems(
      visibleToolbarButtons(toolbarButtons(), [
        "aqe:play",
        "aqe:back-chain-practice",
        "aqe:back-chain-next",
        "aqe:settings",
      ]),
    );
    const panels = items.filter((item) => item.kind === "toolbar-panel");

    expect(panels).toEqual([
      expect.objectContaining({
        buttons: expect.arrayContaining([
          expect.objectContaining({ command: "aqe:back-chain-practice" }),
          expect.objectContaining({ command: "aqe:back-chain-next" }),
        ]),
        definition: expect.objectContaining({ slug: "back-chaining" }),
      }),
    ]);
    expect(panels[0]?.buttons.map((button) => button.command)).toEqual([
      "aqe:back-chain-practice",
      "aqe:back-chain-next",
    ]);
  });
});
