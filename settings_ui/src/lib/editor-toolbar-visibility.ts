import { t } from "./i18n.js";
import {
  DEFAULT_VISIBLE_EDITOR_BUTTONS,
  toolbarButtons,
} from "./editor-toolbar-buttons.js";
import { COMMAND_SLUGS } from "./editor-toolbar-command-slugs.js";
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

const BACK_CHAINING_PANEL_COMMANDS = [
  "aqe:back-chain-practice",
  "aqe:back-chain-previous",
  "aqe:back-chain-next",
] as const satisfies readonly EditorCommand[];

const ATOMIC_PANEL_COMMAND_GROUPS = [
  BACK_CHAINING_PANEL_COMMANDS,
  RECORDING_PANEL_COMMANDS,
] as const;

export function toolbarPanels(
  buttons: readonly ToolbarButtonSpec[] = toolbarButtons(),
): readonly ToolbarPanelSpec[] {
  const panels: ToolbarPanelSpec[] = [];
  for (let index = 0; index < buttons.length; index += 1) {
    const button = buttons[index];
    if (!button) continue;
    const next = buttons[index + 1];
    const afterNext = buttons[index + 2];
    if (
      button.command === "aqe:back-chain-practice"
      && next?.command === "aqe:back-chain-previous"
      && afterNext?.command === "aqe:back-chain-next"
    ) {
      panels.push({
        buttons: [button, next, afterNext],
        commands: [button.command, next.command, afterNext.command],
        icon: button.icon,
        label: t("editor.back_chaining.title"),
        primaryButton: button,
        slug: "back-chaining",
        title: t("editor.command.back_chain_practice.title"),
      });
      index += 2;
      continue;
    }
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
  for (const commands of ATOMIC_PANEL_COMMAND_GROUPS) {
    if (commands.some((command) => requested.has(command))) {
      for (const command of commands) {
        if (availableCommands.has(command)) requested.add(command);
      }
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
