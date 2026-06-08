import { describe, expect, it } from "vitest";

import { toolbarButtons, type EditorCommand } from "../src/lib/editor-toolbar-buttons.js";
import {
  TOOLBAR_PANEL_DEFINITIONS,
  toolbarPanelDefinitionAt,
} from "../src/lib/editor-toolbar-panel-definitions.js";
import { normalizeVisibleEditorButtons, toolbarPanels } from "../src/lib/editor-toolbar-visibility.js";
import { settingsToolbarButtons } from "../src/lib/settings-toolbar-buttons.js";

describe("editor toolbar visibility panels", () => {
  it("defines toolbar commands in the configured sequence", () => {
    expect(toolbarButtons().map((button) => button.command)).toEqual([
      "aqe:play",
      "aqe:analyze",
      "aqe:show-file",
      "aqe:share",
      "aqe:denoise-standard",
      "aqe:remove-pauses",
      "aqe:slower",
      "aqe:faster",
      "aqe:volume-down",
      "aqe:volume-up",
      "aqe:chorusing-practice",
      "aqe:chorusing-next",
      "aqe:chorusing-previous",
      "aqe:record-voice",
      "aqe:play-recording",
      "aqe:share-recording",
      "aqe:show-recording-file",
      "aqe:pitch-hum",
      "aqe:convert",
      "aqe:reduce-size",
      "aqe:undo",
      "aqe:redo",
      "aqe:settings",
    ]);

    expect(settingsToolbarButtons().map((button) => button.command)).toEqual([
      "aqe:play",
      "aqe:analyze",
      "aqe:show-file",
      "aqe:share",
      "aqe:denoise-standard",
      "aqe:remove-pauses",
      "aqe:slower",
      "aqe:faster",
      "aqe:volume-down",
      "aqe:volume-up",
      "aqe:chorusing-practice",
      "aqe:chorusing-next",
      "aqe:chorusing-previous",
      "aqe:record-voice",
      "aqe:play-recording",
      "aqe:share-recording",
      "aqe:show-recording-file",
      "aqe:pitch-hum",
      "aqe:convert",
      "aqe:reduce-size",
      "aqe:delete-selection",
      "aqe:delete-rest",
      "aqe:undo",
      "aqe:redo",
      "aqe:settings",
    ]);
  });

  it("defines atomic toolbar panels in one shared list", () => {
    expect(TOOLBAR_PANEL_DEFINITIONS.map((definition) => ({
      commands: definition.commands,
      descriptionKey: definition.descriptionKey,
      labelKey: definition.labelKey,
      slug: definition.slug,
      titleKey: definition.titleKey,
    }))).toEqual([
      {
        commands: [
          "aqe:chorusing-practice",
          "aqe:chorusing-next",
          "aqe:chorusing-previous",
        ],
        descriptionKey: "editor.chorusing.panel_description",
        labelKey: "editor.chorusing.title",
        slug: "chorusing",
        titleKey: "editor.command.chorusing_practice.title",
      },
      {
        commands: [
          "aqe:record-voice",
          "aqe:play-recording",
          "aqe:share-recording",
          "aqe:show-recording-file",
        ],
        descriptionKey: "editor.recording.panel_description",
        labelKey: "editor.command.record_group.label",
        slug: "record-play-yours",
        titleKey: "editor.command.record_group.label",
      },
    ]);
  });

  it("matches shared panel definitions against consecutive toolbar buttons", () => {
    const buttons = toolbarButtons();
    const chorusingIndex = buttons.findIndex((button) => button.command === "aqe:chorusing-practice");
    const recordingIndex = buttons.findIndex((button) => button.command === "aqe:record-voice");

    expect(toolbarPanelDefinitionAt(buttons, chorusingIndex)?.definition.slug).toBe("chorusing");
    expect(toolbarPanelDefinitionAt(buttons, recordingIndex)?.definition.slug).toBe("record-play-yours");
    expect(toolbarPanelDefinitionAt(buttons, 0)).toBeUndefined();
  });

  it("groups chorusing commands into one settings panel", () => {
    const panels = toolbarPanels(toolbarButtons());
    const chorusingPanel = panels.find((panel) => panel.slug === "chorusing");

    expect(chorusingPanel?.commands).toEqual([
      "aqe:chorusing-practice",
      "aqe:chorusing-next",
      "aqe:chorusing-previous",
    ]);
    expect(panels.filter((panel) => panel.commands.includes("aqe:chorusing-previous"))).toHaveLength(1);
  });

  it("preserves partial chorusing visibility", () => {
    expect(
      normalizeVisibleEditorButtons(
        toolbarButtons(),
        ["aqe:play", "aqe:chorusing-next", "aqe:settings"] as EditorCommand[],
      ),
    ).toEqual([
      "aqe:play",
      "aqe:chorusing-next",
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
      "aqe:share-recording",
      "aqe:show-recording-file",
      "aqe:settings",
    ]);
  });
});
