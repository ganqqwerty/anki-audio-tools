<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import AqeTooltipProvider from "../lib/AqeTooltipProvider.svelte";
  import { toolbarButtons, visibleToolbarButtons } from "./commands.js";
  import { buttonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import type { ToolbarPanelSlug } from "../lib/editor-toolbar-panel-definitions.js";
  import { t } from "../lib/i18n.js";
  import { buildEditorToolbarRenderItems } from "./editor-toolbar-render-items.js";
  import EditorHelp from "./EditorHelp.svelte";
  import EditorToolbarButton from "./EditorToolbarButton.svelte";
  import EditorToolbarPanel from "./EditorToolbarPanel.svelte";
  import GraphVisualizer from "./GraphVisualizer.svelte";
  import PlaySplitButton from "./PlaySplitButton.svelte";
  import SplitButton from "./SplitButton.svelte";
  import { historyAvailability } from "./actions.js";
  import type { FieldTarget } from "./types.js";

  const TOOLBAR_PANEL_CLASSES: Record<ToolbarPanelSlug, string> = {
    "back-chaining": "aqe-back-chaining-toolbar-panel",
    "record-play-yours": "aqe-recording-group",
  };

  const TOOLBAR_PANEL_TEST_ID_PREFIXES: Record<ToolbarPanelSlug, string> = {
    "back-chaining": "back-chaining",
    "record-play-yours": "recording",
  };

  const { target }: { target: FieldTarget } = $props();
  const repeatDefault = window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;
  const repeatPauseDefault = window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.repeatPauseSeconds ?? 0;
  const buttons = visibleToolbarButtons(
    toolbarButtons(),
    window.__AQE_EDITOR_CONFIG__?.visibleEditorButtons,
  );
  const buttonModes = window.__AQE_EDITOR_CONFIG__?.editorButtonModes;
  const renderItems = buildEditorToolbarRenderItems(buttons);

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
    if (command === "aqe:back-chain-practice") return t("editor.command.back_chain_practice.disabled_title");
    if (command === "aqe:back-chain-previous") return t("editor.command.back_chain_previous.disabled_title");
    if (command === "aqe:back-chain-next") return t("editor.command.back_chain_next.disabled_title");
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

  function toolbarPanelClass(slug: ToolbarPanelSlug): string {
    return TOOLBAR_PANEL_CLASSES[slug];
  }

  function toolbarPanelTestId(slug: ToolbarPanelSlug): string {
    return `aqe-${TOOLBAR_PANEL_TEST_ID_PREFIXES[slug]}-toolbar-panel-${target.ord}`;
  }

</script>

<AqeTooltipProvider>
  <div
    class="aqe-controls"
    data-aqe-field-ord={target.ord}
    data-aqe-source-filename={target.sourceFilename}
    data-testid={`aqe-controls-${target.ord}`}
  >
    {#each renderItems as item (item.kind === "split-run-group" ? `${item.menuSlug}:${item.buttons[0].command}` : item.kind === "toolbar-panel" ? `${item.definition.slug}:${item.buttons[0]?.command}` : item.button.command)}
      {#if item.kind === "split-run-group"}
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
      {:else if item.kind === "toolbar-panel"}
        <EditorToolbarPanel
          label={item.label}
          panelClass={toolbarPanelClass(item.definition.slug)}
          testId={toolbarPanelTestId(item.definition.slug)}
        >
          {#if item.definition.slug === "record-play-yours"}
            {@const record = item.buttons.find((button) => button.command === "aqe:record-voice")}
            {@const playRecording = item.buttons.find((button) => button.command === "aqe:play-recording")}
            {#if record && playRecording}
              <span class="aqe-split-group">
                <SplitButton
                  button={record}
                  displayMode={buttonDisplayMode(record.command, buttonModes)}
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
                  button={record}
                  displayMode={buttonDisplayMode(record.command, buttonModes)}
                  groupLabel={item.label}
                  showPrimary={false}
                  showRunButton={false}
                  {target}
                />
              </span>
            {/if}
          {:else}
            {#each item.buttons as button (button.command)}
              <EditorToolbarButton
                {button}
                displayMode={buttonDisplayMode(button.command, buttonModes)}
                disabled={initialButtonDisabled(button.command)}
                disabledTitle={disabledTitle(button.command)}
                {target}
              />
            {/each}
          {/if}
        </EditorToolbarPanel>
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
