<script lang="ts">
  import { Popover } from "bits-ui";
  import { onMount } from "svelte";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import GraphSplitOptions from "./GraphSplitOptions.svelte";
  import SplitValueOptions from "./SplitValueOptions.svelte";
  import { send } from "./actions.js";
  import { sendSplitDefaultSaveRequest } from "./bridge.js";
  import {
    buildSplitCommandPayload,
    buildSplitDefaultSaveRequest,
    formatOutputFormat,
    formatDenoiseAlgorithm,
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
    formatGraphRecordingCondition,
    formatGraphSmoothness,
    formatGraphVoiceLock,
    formatGraphVoiceRange,
  } from "./graph-split-values.js";
  import {
    setGraphConnectShortDropoutsForField,
    setGraphRecordingConditionForField,
    setGraphSmoothnessForField,
    setGraphVoiceLockForField,
    setGraphVoiceRangeForField,
  } from "./graph-split-state.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import { t } from "../lib/i18n.js";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import { EditorButtonMode } from "../lib/types.js";
  import type { GraphRecordingCondition, GraphSmoothness, GraphVoiceLock, GraphVoiceRange } from "./graph-settings.js";
  import type { ButtonSpec, FieldSplitButtonState, FieldTarget } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type OutputFormatValue = FieldSplitButtonState["outputFormat"];
  type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
  type ShareTarget = FieldSplitButtonState["shareTarget"];

  const { button, displayMode, target }: {
    button: ButtonSpec;
    displayMode: EditorButtonDisplayMode;
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
  function slug(): string { return COMMAND_SLUGS[button.command]; }
  function initialButtonState(): string {
    if (button.command === "aqe:play") return "play";
    if (button.command === "aqe:analyze") return "graph";
    return "default";
  }
  function isDenoiseButton(): boolean {
    return (
      button.command === "aqe:denoise-standard" ||
      button.command === "aqe:rnnoise" ||
      button.command === "aqe:dpdfnet" ||
      button.command === "aqe:voice-only"
    );
  }
  function primaryTitle(): string {
    if (button.command === "aqe:convert") {
      return t("editor.command.convert.title", { format: formatOutputFormat(outputFormat) });
    }
    if (!isDenoiseButton()) return button.title;
    return t("editor.command.denoise.title", { algorithm: formatDenoiseAlgorithm(denoiseAlgorithm) });
  }
  const graphSummary = $derived([formatGraphVoiceRange(graphVoiceRange), formatGraphRecordingCondition(graphRecordingCondition), formatGraphSmoothness(graphSmoothness), `${graphConnectShortDropoutsMs} ms`, formatGraphVoiceLock(graphVoiceLock)].join(" · "));

  function currentValueLabel(): string {
    if (button.command === "aqe:volume-up" || button.command === "aqe:volume-down") return `${volumeStepDb % 1 === 0 ? volumeStepDb.toFixed(0) : volumeStepDb.toFixed(1)} dB`;
    if (button.command === "aqe:faster" || button.command === "aqe:slower") return `x${(button.command === "aqe:slower" ? 1 - speedStep : 1 + speedStep).toFixed(2)}`;
    if (button.command === "aqe:remove-pauses") return pauseAggressiveness === "aggressive"
      ? t("settings.pause_aggressiveness.aggressive")
      : pauseAggressiveness === "gentle"
        ? t("settings.pause_aggressiveness.gentle")
        : t("settings.pause_aggressiveness.normal");
    if (button.command === "aqe:convert") return formatOutputFormat(outputFormat);
    if (button.command === "aqe:share") return shareTarget === "litterbox"
      ? t("editor.share.target.litterbox")
      : t("editor.share.target.catbox");
    if (button.command === "aqe:pitch-hum") return pitchHumMode === "pitch_tier"
      ? t("editor.pitch_hum.mode.pitch_tier")
      : t("editor.pitch_hum.mode.direct");
    if (
      button.command === "aqe:denoise-standard" ||
      button.command === "aqe:rnnoise" ||
      button.command === "aqe:dpdfnet" ||
      button.command === "aqe:voice-only"
    ) {
      return denoiseAlgorithm === "dpdfnet"
        ? `${formatDenoiseAlgorithm(denoiseAlgorithm)} (${t(`settings.pause_aggressiveness.${dpdfnetAttnLimitDb === 6 ? "gentle" : dpdfnetAttnLimitDb === 18 ? "aggressive" : "normal"}`)})`
        : formatDenoiseAlgorithm(denoiseAlgorithm);
    }
    if (button.command === "aqe:analyze") return graphSummary;
    return "";
  }

  function menuTitle(): string {
    return t("editor.split.menu_title", {
      label: button.label,
      value: currentValueLabel(),
    });
  }

  function popoverDescription(): string {
    if (button.command === "aqe:analyze") {
      return t("editor.split.description_graph", { value: graphSummary });
    }
    return t("editor.split.description", {
      label: button.label,
      value: currentValueLabel(),
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
    return () => {
      if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    };
  });
</script>

<Popover.Root open={open} onOpenChange={onOpenChange}>
  <span class="aqe-split-button">
    <button
      type="button"
      class:aqe-icon-only={displayMode === EditorButtonMode.Icon}
      class="aqe-button aqe-split-primary"
      data-aqe-command={button.command}
      data-aqe-button-state={initialButtonState()}
      data-testid={`aqe-button-${target.ord}-${slug()}`}
      title={primaryTitle()}
      aria-label={primaryTitle()}
      onmousedown={(event) => event.preventDefault()}
      onclick={dispatchPrimary}
    >
      {#if displayMode === EditorButtonMode.Icon}
        <EditorCommandIcon icon={button.icon} />
      {/if}
      <span class="aqe-button-label">{button.label}</span>
    </button>
    <Popover.Trigger
      class="aqe-button aqe-icon-only aqe-split-menu-button"
      data-testid={`aqe-split-${target.ord}-${slug()}-menu`}
      title={menuTitle()}
      aria-label={menuTitle()}
      onmousedown={(event) => event.preventDefault()}
    >
      <EditorCommandIcon icon="chevron-down" />
      <span class="aqe-button-label">{t("editor.split.options")}</span>
    </Popover.Trigger>
    <Popover.Content
      align="center"
      arrowPadding={14}
      class={`aqe-split-popover${button.command === "aqe:analyze" ? " aqe-graph-split-popover" : ""}`}
      collisionPadding={8}
      data-testid={`aqe-split-${target.ord}-${slug()}-popover`}
      onCloseAutoFocus={(event) => event.preventDefault()}
      side="bottom"
      sideOffset={4}
      strategy="fixed"
      trapFocus={false}
    >
      <Popover.Arrow
        class="aqe-split-popover-arrow"
        data-testid={`aqe-split-${target.ord}-${slug()}-arrow`}
        height={8}
        width={16}
      />
      {#if button.command === "aqe:analyze"}
        <div class="aqe-split-popover-header aqe-split-popover-header-with-action">
          <span class="aqe-split-popover-title">
            <strong>{button.label}</strong>
          </span>
          <SplitDefaultSaveButton
            onSave={saveCurrentDefaults}
            saved={defaultSaved}
            testId={`aqe-split-${target.ord}-${slug()}-save-default`}
          />
        </div>
        <p class="aqe-split-popover-description">{popoverDescription()}</p>
        <GraphSplitOptions
          connectShortDropoutsMs={graphConnectShortDropoutsMs}
          onConnectShortDropouts={applyGraphConnectShortDropouts}
          onRecordingCondition={applyGraphRecordingCondition}
          onSmoothness={applyGraphSmoothness}
          onVoiceLock={applyGraphVoiceLock}
          onVoiceRange={applyGraphVoiceRange}
          recordingCondition={graphRecordingCondition}
          slug={slug()}
          smoothness={graphSmoothness}
          targetOrd={target.ord}
          voiceLock={graphVoiceLock}
          voiceRange={graphVoiceRange}
        />
        <div class="aqe-split-popover-footer">
          <button
            type="button"
            class="aqe-button aqe-split-run-button"
            data-testid={`aqe-split-${target.ord}-${slug()}-run`}
            title={t("editor.split.run_title", { label: button.label })}
            aria-label={t("editor.split.run_title", { label: button.label })}
            onclick={dispatchPrimary}
          >
            {t("editor.split.run")}
          </button>
        </div>
      {:else}
        <SplitValueOptions
          {button}
          denoiseAlgorithm={denoiseAlgorithm}
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
          dpdfnetAttnLimitDb={dpdfnetAttnLimitDb}
          outputFormat={outputFormat}
          pitchHumMode={pitchHumMode}
          saveDefaultSaved={defaultSaved}
          shareTarget={shareTarget}
          showSaveDefault={button.command !== "aqe:share"}
          speedStep={speedStep}
          targetOrd={target.ord}
          volumeStepDb={volumeStepDb}
        />
      {/if}
    </Popover.Content>
  </span>
</Popover.Root>
