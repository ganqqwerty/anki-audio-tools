<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import AqeTooltipProvider from "../lib/AqeTooltipProvider.svelte";
  import { toolbarButtons, visibleToolbarButtons } from "./commands.js";
  import { buttonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import { t } from "../lib/i18n.js";
  import EditorHelp from "./EditorHelp.svelte";
  import EditorToolbarButton from "./EditorToolbarButton.svelte";
  import GraphVisualizer from "./GraphVisualizer.svelte";
  import PlaySplitButton from "./PlaySplitButton.svelte";
  import SplitButton from "./SplitButton.svelte";
  import { historyAvailability } from "./actions.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";

  type ToolbarRenderItem =
    | { button: ButtonSpec; kind: "button" }
    | {
      buttons: readonly [ButtonSpec, ButtonSpec, ButtonSpec];
      kind: "back-chaining-group";
      label: string;
    }
    | {
      buttons: readonly [ButtonSpec, ButtonSpec];
      kind: "group";
      menuLabel: string;
      menuSlug: "speed" | "volume";
    }
    | {
      playRecording: ButtonSpec;
      record: ButtonSpec;
      kind: "recording-group";
    };

  const { target }: { target: FieldTarget } = $props();
  const repeatDefault = window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;
  const repeatPauseDefault = window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.repeatPauseSeconds ?? 0;
  const buttons = visibleToolbarButtons(
    toolbarButtons(),
    window.__AQE_EDITOR_CONFIG__?.visibleEditorButtons,
  );
  const buttonModes = window.__AQE_EDITOR_CONFIG__?.editorButtonModes;
  const renderItems = buildToolbarRenderItems(buttons);

  function isSplitCommand(command: string): boolean {
    return [
      "aqe:analyze",
      "aqe:record-voice",
      "aqe:share",
      "aqe:convert",
      "aqe:reduce-size",
      "aqe:slower",
      "aqe:faster",
      "aqe:volume-down",
      "aqe:volume-up",
      "aqe:remove-pauses",
      "aqe:denoise-standard",
      "aqe:pitch-hum",
    ].includes(command);
  }

  function disabledTitle(command: string): string | undefined {
    if (command === "aqe:undo") return t("editor.command.undo.disabled_title");
    if (command === "aqe:redo") return t("editor.command.redo.disabled_title");
    return undefined;
  }

  function initialButtonDisabled(command: string): boolean {
    const availability = historyAvailability(target.ord);
    if (command === "aqe:undo") return !availability.canUndo;
    if (command === "aqe:redo") return !availability.canRedo;
    if (command === "aqe:back-chain-next") return true;
    if (command === "aqe:back-chain-previous") return true;
    if (command === "aqe:record-voice" || command === "aqe:play-recording") return true;
    return false;
  }

  function buildToolbarRenderItems(buttons: readonly ButtonSpec[]): readonly ToolbarRenderItem[] {
    const items: ToolbarRenderItem[] = [];
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
        items.push({
          buttons: [button, next, afterNext],
          kind: "back-chaining-group",
          label: t("editor.back_chaining.title"),
        });
        index += 2;
        continue;
      }
      if (button.command === "aqe:record-voice" && next?.command === "aqe:play-recording") {
        items.push({
          kind: "recording-group",
          playRecording: next,
          record: button,
        });
        index += 1;
        continue;
      }
      if (button.command === "aqe:slower" && next?.command === "aqe:faster") {
        items.push({
          buttons: [button, next],
          kind: "group",
          menuLabel: t("editor.split.group.speed"),
          menuSlug: "speed",
        });
        index += 1;
        continue;
      }
      if (button.command === "aqe:volume-down" && next?.command === "aqe:volume-up") {
        items.push({
          buttons: [button, next],
          kind: "group",
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

</script>

<AqeTooltipProvider>
  <div
    class="aqe-controls"
    data-aqe-field-ord={target.ord}
    data-aqe-source-filename={target.sourceFilename}
    data-testid={`aqe-controls-${target.ord}`}
  >
    {#each renderItems as item (item.kind === "group" ? `${item.menuSlug}:${item.buttons[0].command}` : item.kind === "recording-group" ? `recording:${item.record.command}` : item.kind === "back-chaining-group" ? `back-chaining:${item.buttons[0].command}` : item.button.command)}
      {#if item.kind === "group"}
        <span class="aqe-split-group">
          <SplitButton
            button={item.buttons[0]}
            displayMode={buttonDisplayMode(item.buttons[0].command, buttonModes)}
            primaryGroupPosition="start"
            showMenu={false}
            {target}
          />
          <SplitButton
            button={item.buttons[1]}
            displayMode={buttonDisplayMode(item.buttons[1].command, buttonModes)}
            primaryGroupPosition="middle"
            showMenu={false}
            {target}
          />
          <SplitButton
            button={item.buttons[1]}
            displayMode={buttonDisplayMode(item.buttons[1].command, buttonModes)}
            groupLabel={item.menuLabel}
            groupSlug={item.menuSlug}
            showPrimary={false}
            showRunButton={false}
            {target}
          />
        </span>
      {:else if item.kind === "recording-group"}
        {@const playRecording = item.playRecording}
        <span class="aqe-split-group aqe-recording-group">
          <SplitButton
            button={item.record}
            displayMode={buttonDisplayMode(item.record.command, buttonModes)}
            primaryGroupPosition="start"
            showMenu={false}
            {target}
          />
          <SplitButton
            button={playRecording}
            displayMode={buttonDisplayMode(playRecording.command, buttonModes)}
            primaryGroupPosition="middle"
            showMenu={false}
            {target}
          />
          <SplitButton
            button={item.record}
            displayMode={buttonDisplayMode(item.record.command, buttonModes)}
            groupLabel={t("editor.command.record_group.label")}
            showPrimary={false}
            showRunButton={false}
            {target}
          />
        </span>
      {:else if item.kind === "back-chaining-group"}
        <span
          class="aqe-toolbar-panel aqe-back-chaining-toolbar-panel"
          data-testid={`aqe-back-chaining-toolbar-panel-${target.ord}`}
          role="group"
          aria-label={item.label}
        >
          <span class="aqe-toolbar-panel-label" aria-hidden="true">{item.label}</span>
          {#each item.buttons as button (button.command)}
            <EditorToolbarButton
              {button}
              displayMode={buttonDisplayMode(button.command, buttonModes)}
              disabled={initialButtonDisabled(button.command)}
              disabledTitle={disabledTitle(button.command)}
              {target}
            />
          {/each}
        </span>
      {:else if item.button.command === "aqe:play"}
        <PlaySplitButton
          button={item.button}
          displayMode={buttonDisplayMode(item.button.command, buttonModes)}
          {repeatDefault}
          {target}
        />
      {:else if isSplitCommand(item.button.command)}
        <SplitButton
          button={item.button}
          displayMode={buttonDisplayMode(item.button.command, buttonModes)}
          {target}
        />
      {:else}
        {@const button = item.button}
        <EditorToolbarButton
          {button}
          displayMode={buttonDisplayMode(button.command, buttonModes)}
          disabled={initialButtonDisabled(button.command)}
          disabledTitle={disabledTitle(button.command)}
          {target}
        />
      {/if}
    {/each}
    <EditorHelp ord={target.ord} />
    <GraphVisualizer {repeatDefault} {repeatPauseDefault} {target} />
    <div class="aqe-status-row" data-testid={`aqe-status-row-${target.ord}`}>
      <span
        class="aqe-spinner"
        data-testid={`aqe-graph-spinner-${target.ord}`}
        hidden
        aria-hidden="true"
      ></span>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <span
            {...props}
            class="aqe-status aqe-tooltip-target"
            data-testid={`aqe-status-${target.ord}`}
          ></span>
        {/snippet}
      </AqeTooltip>
    </div>
  </div>
</AqeTooltipProvider>
