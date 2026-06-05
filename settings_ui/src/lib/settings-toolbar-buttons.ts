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
  return [...toolbarButtons(), ...selectionActionButtons()] as const;
}
