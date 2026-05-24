<script lang="ts">
  import { Popover } from "bits-ui";
  import { onMount } from "svelte";
  import AqeTooltip from "../lib/AqeTooltip.svelte";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import SplitButtonPrimary from "./SplitButtonPrimary.svelte";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import GraphSplitOptions from "./GraphSplitOptions.svelte";
  import SplitValueOptions from "./SplitValueOptions.svelte";
  import { send } from "./actions.js";
  import { sendSplitDefaultSaveRequest } from "./bridge.js";
  import {
    buildSplitCommandPayload,
    buildSplitDefaultSaveRequest,
    getSplitButtonState,
    promoteSplitDefaultsForField,
    setDenoiseAlgorithmForField,
    setDpdfnetAttnLimitDbForField,
    setOutputFormatForField,
    setPauseAggressivenessForField,
    setPitchHumModeForField,
    setShareTargetForField,
    setSpeedStepForField,
    setVolumeStepForField,
  } from "./split-button-state.js";
  import {
    setGraphConnectShortDropoutsForField,
    setGraphRecordingConditionForField,
    setGraphSmoothnessForField,
    setGraphVoiceLockForField,
    setGraphVoiceRangeForField,
  } from "./graph-split-state.js";
  import { currentValueLabel, primaryTitle } from "./split-button-presenter.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import { t } from "../lib/i18n.js";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import type { GraphRecordingCondition, GraphSmoothness, GraphVoiceLock, GraphVoiceRange } from "./graph-settings.js";
  import type { ButtonSpec, FieldSplitButtonState, FieldTarget } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type OutputFormatValue = FieldSplitButtonState["outputFormat"];
  type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
  type PrimaryGroupPosition = "middle" | "start";
  type ShareTarget = FieldSplitButtonState["shareTarget"];
  const CLOSE_SPLIT_MENUS_EVENT = "aqe-ui:close-split-menus";

  const {
    button,
    displayMode,
    groupLabel,
    groupSlug,
    primaryGroupPosition = "start",
    showMenu = true,
    showPrimary = true,
    showRunButton = true,
    target,
  }: {
    button: ButtonSpec;
    displayMode: EditorButtonDisplayMode;
    groupLabel?: string;
    groupSlug?: "speed" | "volume";
    primaryGroupPosition?: PrimaryGroupPosition;
    showMenu?: boolean;
    showPrimary?: boolean;
    showRunButton?: boolean;
    target: FieldTarget;
  } = $props();

  let open = $state(false);
  let volumeStepDb = $state(3);
  let speedStep = $state(0.05);
  let pauseAggressiveness = $state<"gentle" | "normal" | "aggressive">("normal");
  let denoiseAlgorithm = $state<DenoiseAlgorithm>("standard");
  let dpdfnetAttnLimitDb = $state(12);
  let outputFormat = $state<OutputFormatValue>("mp3");
  let pitchHumMode = $state<PitchHumMode>("direct");
  let shareTarget = $state<ShareTarget>("litterbox");
  let graphVoiceRange = $state<GraphVoiceRange>("general");
  let graphRecordingCondition = $state<GraphRecordingCondition>("auto");
  let graphSmoothness = $state<GraphSmoothness>("very_smooth");
  let graphConnectShortDropoutsMs = $state(240);
  let graphVoiceLock = $state<GraphVoiceLock>("balanced");
  let defaultSaved = $state(false);
  let defaultSavedTimer: number | undefined;

  function slug(): string {
    return COMMAND_SLUGS[button.command];
  }

  function menuSlug(): string {
    return groupSlug ?? slug();
  }

  function menuTextLabel(): string {
    return groupLabel ?? button.label;
  }

  function primaryClass(): string {
    return primaryGroupPosition === "middle"
      ? "aqe-button aqe-split-primary aqe-split-primary-middle"
      : "aqe-button aqe-split-primary";
  }

  const currentPrimaryTitle = $derived(primaryTitle(button, outputFormat, denoiseAlgorithm));
  const currentValue = $derived(currentValueLabel(button, groupSlug, {
    denoiseAlgorithm,
    dpdfnetAttnLimitDb,
    graphConnectShortDropoutsMs,
    graphRecordingCondition,
    graphSmoothness,
    graphVoiceLock,
    graphVoiceRange,
    outputFormat,
    pauseAggressiveness,
    pitchHumMode,
    shareTarget,
    speedStep,
    volumeStepDb,
  }));

  function menuTitle(): string {
    return t("editor.split.menu_title", {
      label: menuTextLabel(),
      value: currentValue,
    });
  }

  function close(): void {
    open = false;
  }

  function syncFromState(state: FieldSplitButtonState): void {
    volumeStepDb = state.volumeStepDb;
    speedStep = state.speedStep;
    pauseAggressiveness = state.pauseAggressiveness;
    denoiseAlgorithm = state.denoiseAlgorithm;
    dpdfnetAttnLimitDb = state.dpdfnetAttnLimitDb;
    outputFormat = state.outputFormat;
    pitchHumMode = state.pitchHumMode;
    shareTarget = state.shareTarget;
    graphVoiceRange = state.graphVoiceRange;
    graphRecordingCondition = state.graphRecordingCondition;
    graphSmoothness = state.graphSmoothness;
    graphConnectShortDropoutsMs = state.graphConnectShortDropoutsMs;
    graphVoiceLock = state.graphVoiceLock;
  }

  function applyVolumeStep(value: number): void {
    volumeStepDb = setVolumeStepForField(target.ord, value).volumeStepDb;
  }

  function applySpeedStep(value: number): void {
    speedStep = setSpeedStepForField(target.ord, value).speedStep;
  }

  function applyPauseAggressiveness(value: "gentle" | "normal" | "aggressive"): void {
    pauseAggressiveness = setPauseAggressivenessForField(target.ord, value).pauseAggressiveness;
  }

  function applyDenoiseAlgorithm(value: DenoiseAlgorithm): void {
    denoiseAlgorithm = setDenoiseAlgorithmForField(target.ord, value).denoiseAlgorithm;
  }

  function applyDpdfnetAttnLimitDb(value: number): void {
    dpdfnetAttnLimitDb = setDpdfnetAttnLimitDbForField(target.ord, value).dpdfnetAttnLimitDb;
  }

  function applyOutputFormat(value: OutputFormatValue): void {
    outputFormat = setOutputFormatForField(target.ord, value).outputFormat;
  }

  function applyPitchHumMode(value: PitchHumMode): void {
    pitchHumMode = setPitchHumModeForField(target.ord, value).pitchHumMode;
  }

  function applyShareTarget(value: ShareTarget): void {
    shareTarget = setShareTargetForField(target.ord, value).shareTarget;
  }

  function applyGraphVoiceRange(value: GraphVoiceRange): void {
    graphVoiceRange = setGraphVoiceRangeForField(target.ord, value).graphVoiceRange;
  }

  function applyGraphRecordingCondition(value: GraphRecordingCondition): void {
    graphRecordingCondition = setGraphRecordingConditionForField(target.ord, value).graphRecordingCondition;
  }

  function applyGraphSmoothness(value: GraphSmoothness): void {
    graphSmoothness = setGraphSmoothnessForField(target.ord, value).graphSmoothness;
  }

  function applyGraphConnectShortDropouts(value: number): void {
    graphConnectShortDropoutsMs = setGraphConnectShortDropoutsForField(target.ord, value).graphConnectShortDropoutsMs;
  }

  function applyGraphVoiceLock(value: GraphVoiceLock): void {
    graphVoiceLock = setGraphVoiceLockForField(target.ord, value).graphVoiceLock;
  }

  function dispatchPrimary(): void {
    window.dispatchEvent(new Event(CLOSE_SPLIT_MENUS_EVENT));
    close();
    send(button.command, target.node, target.ord, buildSplitCommandPayload(button.command, target.ord));
  }

  function showDefaultSaved(): void {
    defaultSaved = true;
    if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    defaultSavedTimer = window.setTimeout(() => {
      defaultSaved = false;
      defaultSavedTimer = undefined;
    }, 1400);
  }

  function saveCurrentDefaults(): void {
    const request = buildSplitDefaultSaveRequest(button.command, target.ord);
    sendSplitDefaultSaveRequest(request);
    syncFromState(promoteSplitDefaultsForField(target.ord, request.defaults));
    showDefaultSaved();
  }

  function onOpenChange(nextOpen: boolean): void {
    if (nextOpen) syncFromState(getSplitButtonState(target.ord));
    open = nextOpen;
  }

  onMount(() => {
    syncFromState(getSplitButtonState(target.ord));
    window.addEventListener(CLOSE_SPLIT_MENUS_EVENT, close);
    return () => {
      window.removeEventListener(CLOSE_SPLIT_MENUS_EVENT, close);
      if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    };
  });
</script>

{#if showMenu}
  <Popover.Root open={open} onOpenChange={onOpenChange}>
    <span class="aqe-split-button">
      {#if showPrimary}
        <SplitButtonPrimary
          ariaLabel={currentPrimaryTitle}
          command={button.command}
          {displayMode}
          icon={button.icon}
          label={button.label}
          onClick={dispatchPrimary}
          ord={target.ord}
          primaryClass={primaryClass()}
          slug={slug()}
          title={currentPrimaryTitle}
        />
      {/if}
      <Popover.Trigger
        class="aqe-button aqe-icon-only aqe-split-menu-button"
        data-aqe-tooltip-content={menuTitle()}
        data-testid={`aqe-split-${target.ord}-${menuSlug()}-menu`}
        aria-label={menuTitle()}
      >
        <EditorCommandIcon icon="chevron-down" />
        <span class="aqe-button-label">{t("editor.split.options")}</span>
      </Popover.Trigger>
      <Popover.Content
        align="center"
        arrowPadding={14}
        class={`aqe-split-popover${button.command === "aqe:analyze" ? " aqe-graph-split-popover" : ""}`}
        collisionPadding={8}
        data-testid={`aqe-split-${target.ord}-${menuSlug()}-popover`}
        onCloseAutoFocus={(event) => event.preventDefault()}
        side="bottom"
        sideOffset={4}
        strategy="fixed"
        trapFocus={false}
      >
        <Popover.Arrow
          class="aqe-split-popover-arrow"
          data-testid={`aqe-split-${target.ord}-${menuSlug()}-arrow`}
          height={8}
          width={16}
        />
        {#if button.command === "aqe:analyze"}
          <div class="aqe-split-popover-header aqe-split-popover-header-with-action">
            <span class="aqe-split-popover-title">
              <strong>{menuTextLabel()}</strong>
            </span>
            <SplitDefaultSaveButton
              onSave={saveCurrentDefaults}
              saved={defaultSaved}
              testId={`aqe-split-${target.ord}-${menuSlug()}-save-default`}
            />
          </div>
          <GraphSplitOptions
            connectShortDropoutsMs={graphConnectShortDropoutsMs}
            onConnectShortDropouts={applyGraphConnectShortDropouts}
            onRecordingCondition={applyGraphRecordingCondition}
            onSmoothness={applyGraphSmoothness}
            onVoiceLock={applyGraphVoiceLock}
            onVoiceRange={applyGraphVoiceRange}
            recordingCondition={graphRecordingCondition}
            slug={menuSlug()}
            smoothness={graphSmoothness}
            targetOrd={target.ord}
            voiceLock={graphVoiceLock}
            voiceRange={graphVoiceRange}
          />
          <div class="aqe-split-popover-footer">
            <AqeTooltip>
              {#snippet trigger({ props })}
                <button
                  {...props}
                  type="button"
                  class="aqe-button aqe-split-run-button aqe-tooltip-target"
                  data-aqe-tooltip-content={t("editor.split.run_title", { label: menuTextLabel() })}
                  data-testid={`aqe-split-${target.ord}-${menuSlug()}-run`}
                  aria-label={t("editor.split.run_title", { label: menuTextLabel() })}
                  onclick={dispatchPrimary}
                >
                  {t("editor.split.run")}
                </button>
              {/snippet}
            </AqeTooltip>
          </div>
        {:else}
          <SplitValueOptions
            {button}
            denoiseAlgorithm={denoiseAlgorithm}
            dpdfnetAttnLimitDb={dpdfnetAttnLimitDb}
            {groupSlug}
            menuLabel={menuTextLabel()}
            onChange={() => {}}
            onDenoiseAlgorithm={applyDenoiseAlgorithm}
            onDpdfnetAttnLimitDb={applyDpdfnetAttnLimitDb}
            onOutputFormat={applyOutputFormat}
            onPauseAggressiveness={applyPauseAggressiveness}
            onPitchHumMode={applyPitchHumMode}
            onRun={dispatchPrimary}
            onSaveDefault={saveCurrentDefaults}
            onShareTarget={applyShareTarget}
            onSpeedStep={applySpeedStep}
            onVolumeStep={applyVolumeStep}
            pauseAggressiveness={pauseAggressiveness}
            outputFormat={outputFormat}
            pitchHumMode={pitchHumMode}
            saveDefaultSaved={defaultSaved}
            shareTarget={shareTarget}
            {showRunButton}
            showSaveDefault={true}
            speedStep={speedStep}
            targetOrd={target.ord}
            volumeStepDb={volumeStepDb}
          />
        {/if}
      </Popover.Content>
    </span>
  </Popover.Root>
{:else if showPrimary}
  <SplitButtonPrimary
    ariaLabel={currentPrimaryTitle}
    command={button.command}
    {displayMode}
    icon={button.icon}
    label={button.label}
    onClick={dispatchPrimary}
    ord={target.ord}
    primaryClass={primaryClass()}
    slug={slug()}
    title={currentPrimaryTitle}
  />
{/if}
