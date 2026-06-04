import { describe, expect, it } from "vitest";

import { toolbarButtons, type EditorCommand } from "../src/lib/editor-toolbar-buttons.js";
import {
  TOOLBAR_PANEL_DEFINITIONS,
  toolbarPanelDefinitionAt,
} from "../src/lib/editor-toolbar-panel-definitions.js";
import { normalizeVisibleEditorButtons, toolbarPanels } from "../src/lib/editor-toolbar-visibility.js";

describe("editor toolbar visibility panels", () => {
  it("defines atomic toolbar panels in one shared list", () => {
    expect(TOOLBAR_PANEL_DEFINITIONS.map((definition) => ({
      commands: definition.commands,
      labelKey: definition.labelKey,
      slug: definition.slug,
      titleKey: definition.titleKey,
    }))).toEqual([
      {
        commands: [
          "aqe:back-chain-practice",
          "aqe:back-chain-previous",
          "aqe:back-chain-next",
        ],
        labelKey: "editor.back_chaining.title",
        slug: "back-chaining",
        titleKey: "editor.command.back_chain_practice.title",
      },
      {
        commands: [
          "aqe:record-voice",
          "aqe:play-recording",
        ],
        labelKey: "editor.command.record_group.label",
        slug: "record-play-yours",
        titleKey: "editor.command.record_group.label",
      },
    ]);
  });

  it("matches shared panel definitions against consecutive toolbar buttons", () => {
    const buttons = toolbarButtons();
    const backChainingIndex = buttons.findIndex((button) => button.command === "aqe:back-chain-practice");
    const recordingIndex = buttons.findIndex((button) => button.command === "aqe:record-voice");

    expect(toolbarPanelDefinitionAt(buttons, backChainingIndex)?.definition.slug).toBe("back-chaining");
    expect(toolbarPanelDefinitionAt(buttons, recordingIndex)?.definition.slug).toBe("record-play-yours");
    expect(toolbarPanelDefinitionAt(buttons, 0)).toBeUndefined();
  });

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

  it("preserves partial back-chaining visibility", () => {
    expect(
      normalizeVisibleEditorButtons(
        toolbarButtons(),
        ["aqe:play", "aqe:back-chain-next", "aqe:settings"] as EditorCommand[],
      ),
    ).toEqual([
      "aqe:play",
      "aqe:back-chain-next",
      "aqe:settings",
    ]);
  });

  it("normalizes partial learner recording visibility to the full panel", () => {
    expect(
      normalizeVisibleEditorButtons(
        toolbarButtons(),
        ["aqe:play", "aqe:play-recording", "aqe:settings"] as EditorCommand[],
      ),
    ).toEqual([
      "aqe:play",
      "aqe:record-voice",
      "aqe:play-recording",
      "aqe:settings",
    ]);
  });
});
