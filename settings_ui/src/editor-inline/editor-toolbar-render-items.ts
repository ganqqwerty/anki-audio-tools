import {
  TOOLBAR_PANEL_DEFINITIONS,
  toolbarPanelDefinitionAt,
  type MatchedToolbarPanel,
  type ToolbarPanelDefinition,
} from "../lib/editor-toolbar-panel-definitions.js";
import { t } from "../lib/i18n.js";
import type { ButtonSpec } from "./types.js";

export type ToolbarRenderItem =
  | { button: ButtonSpec; kind: "button" }
  | {
    buttons: readonly ButtonSpec[];
    definition: ToolbarPanelDefinition;
    kind: "toolbar-panel";
    label: string;
  }
  | {
    buttons: readonly [ButtonSpec, ButtonSpec];
    kind: "split-run-group";
    menuLabel: string;
    menuSlug: "speed" | "volume";
  };

export function buildEditorToolbarRenderItems(buttons: readonly ButtonSpec[]): readonly ToolbarRenderItem[] {
  const items: ToolbarRenderItem[] = [];
  for (let index = 0; index < buttons.length; index += 1) {
    const button = buttons[index];
    if (!button) continue;
    const matchedPanel = toolbarPanelRenderItemAt(buttons, index);
    if (matchedPanel) {
      items.push({
        buttons: matchedPanel.buttons,
        definition: matchedPanel.definition,
        kind: "toolbar-panel",
        label: t(matchedPanel.definition.labelKey),
      });
      index += matchedPanel.buttons.length - 1;
      continue;
    }
    const next = buttons[index + 1];
    if (button.command === "aqe:slower" && next?.command === "aqe:faster") {
      items.push({
        buttons: [button, next],
        kind: "split-run-group",
        menuLabel: t("editor.split.group.speed"),
        menuSlug: "speed",
      });
      index += 1;
      continue;
    }
    if (button.command === "aqe:volume-down" && next?.command === "aqe:volume-up") {
      items.push({
        buttons: [button, next],
        kind: "split-run-group",
        menuLabel: t("editor.split.group.volume"),
        menuSlug: "volume",
      });
      index += 1;
      continue;
    }
    items.push({ button, kind: "button" });
  }
  return items;
}

function toolbarPanelRenderItemAt(
  buttons: readonly ButtonSpec[],
  index: number,
): MatchedToolbarPanel<ButtonSpec> | undefined {
  return toolbarPanelDefinitionAt(buttons, index) ?? partialToolbarPanelDefinitionAt(buttons, index);
}

function partialToolbarPanelDefinitionAt(
  buttons: readonly ButtonSpec[],
  index: number,
): MatchedToolbarPanel<ButtonSpec> | undefined {
  const button = buttons[index];
  if (!button) return undefined;

  for (const definition of TOOLBAR_PANEL_DEFINITIONS) {
    if (
      definition.atomicVisibility === true ||
      !definition.commands.some((command) => command === button.command)
    ) {
      continue;
    }
    const panelButtons = definition.commands
      .map((command) => buttons.find((candidate) => candidate.command === command))
      .filter((candidate): candidate is ButtonSpec => candidate !== undefined);
    if (panelButtons[0]?.command !== button.command) continue;
    return { buttons: panelButtons, definition };
  }
  return undefined;
}
