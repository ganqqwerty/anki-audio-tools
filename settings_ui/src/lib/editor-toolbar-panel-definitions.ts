import type { EditorCommand, ToolbarButtonSpec } from "./editor-toolbar-buttons.js";

export type ToolbarPanelSlug = "back-chaining" | "record-play-yours";

export interface ToolbarPanelDefinition {
  atomicVisibility?: boolean;
  commands: readonly EditorCommand[];
  labelKey: string;
  primaryCommand: EditorCommand;
  slug: ToolbarPanelSlug;
  titleKey: string;
}

export interface MatchedToolbarPanel<TButton extends { command: EditorCommand }> {
  buttons: readonly TButton[];
  definition: ToolbarPanelDefinition;
}

export const TOOLBAR_PANEL_DEFINITIONS = [
  {
    atomicVisibility: false,
    commands: [
      "aqe:back-chain-practice",
      "aqe:back-chain-previous",
      "aqe:back-chain-next",
    ],
    labelKey: "editor.back_chaining.title",
    primaryCommand: "aqe:back-chain-practice",
    slug: "back-chaining",
    titleKey: "editor.command.back_chain_practice.title",
  },
  {
    atomicVisibility: true,
    commands: [
      "aqe:record-voice",
      "aqe:play-recording",
    ],
    labelKey: "editor.command.record_group.label",
    primaryCommand: "aqe:record-voice",
    slug: "record-play-yours",
    titleKey: "editor.command.record_group.label",
  },
] as const satisfies readonly ToolbarPanelDefinition[];

export function toolbarPanelDefinitionAt<TButton extends Pick<ToolbarButtonSpec, "command">>(
  buttons: readonly TButton[],
  index: number,
): MatchedToolbarPanel<TButton> | undefined {
  for (const definition of TOOLBAR_PANEL_DEFINITIONS) {
    const matches = definition.commands.every(
      (command, offset) => buttons[index + offset]?.command === command,
    );
    if (matches) {
      return {
        buttons: buttons.slice(index, index + definition.commands.length),
        definition,
      };
    }
  }
  return undefined;
}
