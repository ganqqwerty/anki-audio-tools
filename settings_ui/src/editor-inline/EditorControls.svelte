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
  import type { InitialEditorStatus } from "./control-actions.js";
  import type { FieldTarget } from "./types.js";
  import {
    audioFieldSource,
    editorButtonModes,
    editorRuntimeConfig,
    repeatPlaybackByDefault,
    selectionMarkerShiftButtonsEnabled,
    splitButtonDefaults,
    visibleEditorButtons,
  } from "./editor-runtime-config.js";

  const TOOLBAR_PANEL_CLASSES: Record<ToolbarPanelSlug, string> = {
    "chorusing": "aqe-chorusing-toolbar-panel",
    "record-play-yours": "aqe-recording-group",
  };

  const TOOLBAR_PANEL_TEST_ID_PREFIXES: Record<ToolbarPanelSlug, string> = {
    "chorusing": "chorusing",
    "record-play-yours": "recording",
  };

  const {
    initialStatus = null,
    target,
  }: { initialStatus?: InitialEditorStatus | null; target: FieldTarget } = $props();
  const runtimeConfig = editorRuntimeConfig();
  const defaults = splitButtonDefaults(runtimeConfig);
  const repeatDefault = repeatPlaybackByDefault(runtimeConfig);
  const repeatPauseDefault = defaults.repeatPauseSeconds ?? 0;
  const buttons = visibleToolbarButtons(
    toolbarButtons(runtimeConfig),
    visibleEditorButtons(runtimeConfig),
  );
  const buttonModes = editorButtonModes(runtimeConfig);
  const visibleCommands = visibleEditorButtons(runtimeConfig);
  const markerShiftEnabled = selectionMarkerShiftButtonsEnabled(runtimeConfig);
  const sourceFilename = $derived(audioFieldSource(runtimeConfig, target.ord));
  const renderItems = buildEditorToolbarRenderItems(buttons);
  const initialStatusKind = $derived(initialStatus?.kind || "info");
  const initialStatusMessage = $derived(initialStatus?.message || "");

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
    if (command === "aqe:chorusing-practice") return t("editor.command.chorusing_practice.disabled_title");
    if (command === "aqe:chorusing-previous") return t("editor.command.chorusing_previous.disabled_title");
    if (command === "aqe:chorusing-next") return t("editor.command.chorusing_next.disabled_title");
    return undefined;
  }

  function initialButtonDisabled(command: string): boolean {
    const availability = historyAvailability(target.ord);
    if (command === "aqe:undo") return !availability.canUndo;
    if (command === "aqe:redo") return !availability.canRedo;
    if (command === "aqe:chorusing-next") return true;
    if (command === "aqe:chorusing-previous") return true;
    if (
      command === "aqe:record-voice" ||
      command === "aqe:play-recording" ||
      command === "aqe:share-recording" ||
      command === "aqe:show-recording-file"
    ) return true;
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
            {sourceFilename}
            {target}
          />
          <SplitButton
            button={item.buttons[1]}
            displayMode={buttonDisplayMode(item.buttons[1].command, buttonModes)}
            primaryGroupPosition="middle"
            showMenu={false}
            {sourceFilename}
            {target}
          />
          <SplitButton
            button={item.buttons[1]}
            displayMode={buttonDisplayMode(item.buttons[1].command, buttonModes)}
            groupLabel={item.menuLabel}
            groupSlug={item.menuSlug}
            showPrimary={false}
            showRunButton={false}
            {sourceFilename}
            {target}
          />
        </span>
      {:else if item.kind === "toolbar-panel"}
        <EditorToolbarPanel
          description={item.description}
          label={item.label}
          panelClass={toolbarPanelClass(item.definition.slug)}
          testId={toolbarPanelTestId(item.definition.slug)}
        >
          {#if item.definition.slug === "record-play-yours"}
            {@const record = item.buttons.find((button) => button.command === "aqe:record-voice")}
            {@const playRecording = item.buttons.find((button) => button.command === "aqe:play-recording")}
            {@const shareRecording = item.buttons.find((button) => button.command === "aqe:share-recording")}
            {@const showRecordingFile = item.buttons.find((button) => button.command === "aqe:show-recording-file")}
            {#if record && playRecording && shareRecording && showRecordingFile}
              <span class="aqe-split-group">
                <SplitButton
                  button={record}
                  displayMode={buttonDisplayMode(record.command, buttonModes)}
                  primaryGroupPosition="start"
                  showMenu={false}
                  {sourceFilename}
                  {target}
                />
                <SplitButton
                  button={playRecording}
                  displayMode={buttonDisplayMode(playRecording.command, buttonModes)}
                  primaryGroupPosition="middle"
                  showMenu={false}
                  {sourceFilename}
                  {target}
                />
                <SplitButton
                  button={shareRecording}
                  displayMode={buttonDisplayMode(shareRecording.command, buttonModes)}
                  primaryGroupPosition="middle"
                  showMenu={false}
                  {sourceFilename}
                  {target}
                />
                <SplitButton
                  button={showRecordingFile}
                  displayMode={buttonDisplayMode(showRecordingFile.command, buttonModes)}
                  primaryGroupPosition="middle"
                  showMenu={false}
                  {sourceFilename}
                  {target}
                />
                <SplitButton
                  button={record}
                  displayMode={buttonDisplayMode(record.command, buttonModes)}
                  groupLabel={item.label}
                  showPrimary={false}
                  showRunButton={false}
                  {sourceFilename}
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
          {sourceFilename}
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
    <GraphVisualizer {buttonModes} {repeatDefault} {repeatPauseDefault} selectionMarkerShiftButtonsEnabled={markerShiftEnabled} {target} visibleCommands={visibleCommands} />
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
            data-kind={initialStatusKind}
            data-status-owner="edit"
            data-stable-kind={initialStatusKind}
            data-stable-message={initialStatusMessage}
            data-testid={`aqe-status-${target.ord}`}
          >{initialStatusMessage}</span>
        {/snippet}
      </AqeTooltip>
    </div>
  </div>
</AqeTooltipProvider>
