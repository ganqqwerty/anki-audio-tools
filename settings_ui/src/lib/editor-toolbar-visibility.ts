import { t } from "./i18n.js";
import {
  DEFAULT_VISIBLE_EDITOR_BUTTONS,
  toolbarButtons,
} from "./editor-toolbar-buttons.js";
import {
  TOOLBAR_PANEL_DEFINITIONS,
  toolbarPanelDefinitionAt,
} from "./editor-toolbar-panel-definitions.js";
import { COMMAND_SLUGS } from "./editor-toolbar-command-slugs.js";
import type { CommandIconName } from "./icon-types.js";
import type { EditorCommand, ToolbarButtonSpec } from "./editor-toolbar-buttons.js";

export interface ToolbarPanelSpec {
  atomicVisibility: boolean;
  buttons: readonly ToolbarButtonSpec[];
  commands: readonly EditorCommand[];
  icon: CommandIconName;
  label: string;
  primaryButton: ToolbarButtonSpec;
  slug: string;
  title: string;
}

export function toolbarPanels(
  buttons: readonly ToolbarButtonSpec[] = toolbarButtons(),
): readonly ToolbarPanelSpec[] {
  const panels: ToolbarPanelSpec[] = [];
  for (let index = 0; index < buttons.length; index += 1) {
    const button = buttons[index];
    if (!button) continue;
    const matchedPanel = toolbarPanelDefinitionAt(buttons, index);
    if (matchedPanel) {
      const primaryButton = matchedPanel.buttons.find(
        (candidate) => candidate.command === matchedPanel.definition.primaryCommand,
      ) ?? matchedPanel.buttons[0]!;
      panels.push({
        atomicVisibility: matchedPanel.definition.atomicVisibility === true,
        buttons: matchedPanel.buttons,
        commands: matchedPanel.definition.commands,
        icon: primaryButton.icon,
        label: t(matchedPanel.definition.labelKey),
        primaryButton,
        slug: matchedPanel.definition.slug,
        title: t(matchedPanel.definition.titleKey),
      });
      index += matchedPanel.buttons.length - 1;
      continue;
    }
    panels.push({
      atomicVisibility: false,
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
  for (const definition of TOOLBAR_PANEL_DEFINITIONS) {
    if (definition.atomicVisibility !== true) continue;
    if (definition.commands.some((command) => requested.has(command))) {
      for (const command of definition.commands) {
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
  const recordingDefinition = TOOLBAR_PANEL_DEFINITIONS.find(
    (definition) => definition.slug === "record-play-yours",
  );
  const recordingCommands = new Set<EditorCommand>(recordingDefinition?.commands ?? []);
  return buttons
    .map((button) => button.command)
    .filter((command) => !recordingCommands.has(command));
}
