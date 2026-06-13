import { t } from "./i18n.js";
import { toolbarButtons } from "./editor-toolbar-buttons.js";
import type { ToolbarButtonSpec } from "./editor-toolbar-buttons.js";

export function selectionActionButtons(): readonly ToolbarButtonSpec[] {
  return [
    {
      command: "aqe:delete-selection",
      icon: "selection-remove-inside",
      iconOnly: true,
      label: t("editor.command.delete_region.label"),
      title: t("editor.command.delete_region.title"),
    },
    {
      command: "aqe:delete-rest",
      icon: "selection-remove-outside",
      iconOnly: true,
      label: t("editor.command.delete_rest.label"),
      title: t("editor.command.delete_rest.title"),
    },
  ] as const;
}

export function settingsToolbarButtons(): readonly ToolbarButtonSpec[] {
  const buttons = toolbarButtons();
  const selectionButtons = selectionActionButtons();
  const undoIndex = buttons.findIndex((button) => button.command === "aqe:undo");
  if (undoIndex === -1) return [...buttons, ...selectionButtons] as const;
  return [...buttons.slice(0, undoIndex), ...selectionButtons, ...buttons.slice(undoIndex)] as const;
}
