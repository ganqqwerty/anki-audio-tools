import { t } from "./i18n.js";
import {
  COMMAND_SLUGS,
  DEFAULT_VISIBLE_EDITOR_BUTTONS,
  toolbarButtons,
} from "./editor-toolbar-buttons.js";
import type { CommandIconName } from "./icon-types.js";
import type { EditorCommand, ToolbarButtonSpec } from "./editor-toolbar-buttons.js";

export interface ToolbarPanelSpec {
  buttons: readonly ToolbarButtonSpec[];
  commands: readonly EditorCommand[];
  icon: CommandIconName;
  label: string;
  primaryButton: ToolbarButtonSpec;
  slug: string;
  title: string;
}

const RECORDING_PANEL_COMMANDS = [
  "aqe:record-voice",
  "aqe:play-recording",
] as const satisfies readonly EditorCommand[];

export function toolbarPanels(
  buttons: readonly ToolbarButtonSpec[] = toolbarButtons(),
): readonly ToolbarPanelSpec[] {
  const panels: ToolbarPanelSpec[] = [];
  for (let index = 0; index < buttons.length; index += 1) {
    const button = buttons[index];
    if (!button) continue;
    const next = buttons[index + 1];
    if (button.command === "aqe:record-voice" && next?.command === "aqe:play-recording") {
      panels.push({
        buttons: [button, next],
        commands: [button.command, next.command],
        icon: button.icon,
        label: t("editor.command.record_group.label"),
        primaryButton: button,
        slug: "record-play-yours",
        title: t("editor.command.record_group.label"),
      });
      index += 1;
      continue;
    }
    panels.push({
      buttons: [button],
      commands: [button.command],
      icon: button.icon,
      label: button.label,
      primaryButton: button,
      slug: COMMAND_SLUGS[button.command],
      title: button.title,
    });
  }
  return panels;
}

export function normalizeVisibleEditorButtons(
  buttons: readonly ToolbarButtonSpec[],
  visibleCommands: readonly EditorCommand[] | undefined,
  defaultVisibleCommands: readonly EditorCommand[] = DEFAULT_VISIBLE_EDITOR_BUTTONS,
): readonly EditorCommand[] {
  const sourceCommands = Array.isArray(visibleCommands) ? visibleCommands : defaultVisibleCommands;
  const availableCommands = new Set(buttons.map((button) => button.command));
  const requested = new Set(
    sourceCommands.filter((command): command is EditorCommand => availableCommands.has(command)),
  );
  if (RECORDING_PANEL_COMMANDS.some((command) => requested.has(command))) {
    for (const command of RECORDING_PANEL_COMMANDS) {
      if (availableCommands.has(command)) requested.add(command);
    }
  }
  return buttons.map((button) => button.command).filter((command) => requested.has(command));
}

export function visibleToolbarButtons(
  buttons: readonly ToolbarButtonSpec[],
  visibleCommands: readonly EditorCommand[] | undefined,
): readonly ToolbarButtonSpec[] {
  const normalizedCommands = new Set(
    normalizeVisibleEditorButtons(buttons, visibleCommands, defaultRuntimeVisibleCommands(buttons)),
  );
  return buttons.filter((button) => normalizedCommands.has(button.command));
}

function defaultRuntimeVisibleCommands(buttons: readonly ToolbarButtonSpec[]): readonly EditorCommand[] {
  const recordingCommands = new Set<EditorCommand>(RECORDING_PANEL_COMMANDS);
  return buttons
    .map((button) => button.command)
    .filter((command) => !recordingCommands.has(command));
}
