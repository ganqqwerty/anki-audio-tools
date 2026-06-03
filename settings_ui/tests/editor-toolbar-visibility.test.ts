import { describe, expect, it } from "vitest";

import { toolbarButtons, type EditorCommand } from "../src/lib/editor-toolbar-buttons.js";
import { normalizeVisibleEditorButtons, toolbarPanels } from "../src/lib/editor-toolbar-visibility.js";

describe("editor toolbar visibility panels", () => {
  it("groups back-chaining commands into one settings panel", () => {
    const panels = toolbarPanels(toolbarButtons());
    const backChainingPanel = panels.find((panel) => panel.slug === "back-chaining");

    expect(backChainingPanel?.commands).toEqual([
      "aqe:back-chain-practice",
      "aqe:back-chain-previous",
      "aqe:back-chain-next",
    ]);
    expect(panels.filter((panel) => panel.commands.includes("aqe:back-chain-previous"))).toHaveLength(1);
  });

  it("normalizes partial back-chaining visibility to the full panel", () => {
    expect(
      normalizeVisibleEditorButtons(
        toolbarButtons(),
        ["aqe:play", "aqe:back-chain-next", "aqe:settings"] as EditorCommand[],
      ),
    ).toEqual([
      "aqe:play",
      "aqe:back-chain-practice",
      "aqe:back-chain-previous",
      "aqe:back-chain-next",
      "aqe:settings",
    ]);
  });
});
