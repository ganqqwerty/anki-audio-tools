<script lang="ts">
  import { onMount } from "svelte";

  import SplitButtonPrimary from "./SplitButtonPrimary.svelte";
  import SplitButtonMenu from "./SplitButtonMenu.svelte";
  import { send } from "./actions.js";
  import { dispatchLearnerRecordingPrimary } from "./recording-actions.js";
  import { sendSplitDefaultSaveRequest } from "./bridge.js";
  import {
    buildSplitCommandPayload,
    buildSplitDefaultSaveRequest,
    getSplitButtonState,
    promoteSplitDefaultsForField,
  } from "./split-button-state.js";
  import {
    GRAPH_SPLIT_STATE_CHANGED_EVENT,
    type GraphSplitStateChangedDetail,
  } from "./graph-split-state.js";
  import { currentValueLabel, primaryDisabledReason, primaryInitiallyDisabled, primaryTitle } from "./split-button-presenter.js";
  import { createSplitButtonStateHandlers } from "./split-button-state-behavior.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import { t } from "../lib/i18n.js";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import type { GraphRecordingCondition, GraphSmoothness, GraphVoiceLock, GraphVoiceRange } from "./graph-settings.js";
  import type { ButtonSpec, FieldSplitButtonState, FieldTarget } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type OutputFormatValue = FieldSplitButtonState["outputFormat"];
  type PauseDetectionAlgorithm = FieldSplitButtonState["pauseDetectionAlgorithm"];
  type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
  type SizeReductionMode = FieldSplitButtonState["sizeReductionMode"];
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
    sourceFilename = null,
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
    sourceFilename?: string | null;
    target: FieldTarget;
  } = $props();

  let open = $state(false);
  let volumeStepDb = $state(3);
  let speedStep = $state(0.05);
  let pauseAggressiveness = $state<"gentle" | "normal" | "aggressive">("normal");
  let pauseDetectionAlgorithm = $state<PauseDetectionAlgorithm>("silencedetect");
  let pauseThreshold = $state(-45);
  let pauseMinSilenceSeconds = $state(0.3);
  let pauseMinSpeechSeconds = $state(0.1);
  let pausePreprocessDenoise = $state(true);
  let denoiseAlgorithm = $state<DenoiseAlgorithm>("standard");
  let dpdfnetAttnLimitDb = $state(12);
  let outputFormat = $state<OutputFormatValue>("mp3");
  let sizeReductionMode = $state<SizeReductionMode>("normal");
  let sizeReductionBitrateKbps = $state(64);
  let sizeReductionSampleRateHz = $state(32000);
  let sizeReductionChannels = $state(1);
  let pitchHumMode = $state<PitchHumMode>("direct");
  let shareTarget = $state<ShareTarget>("litterbox");
  let graphVoiceRange = $state<GraphVoiceRange>("general");
  let graphRecordingCondition = $state<GraphRecordingCondition>("auto");
  let graphSmoothness = $state<GraphSmoothness>("very_smooth");
  let graphConnectShortDropoutsMs = $state(240);
  let graphVoiceLock = $state<GraphVoiceLock>("balanced");
  let voiceRecordingCountdownSeconds = $state(0);
  let defaultSaved = $state(false);
  let defaultSavedTimer: number | undefined;
  const targetOrd = $derived(target.ord);
  const targetNode = $derived(target.node);

  const commandSlug = $derived(COMMAND_SLUGS[button.command]);
  const menuSlug = $derived(groupSlug ?? commandSlug);
  const menuTextLabel = $derived(groupLabel ?? button.label);
  const primaryClass = $derived(
    primaryGroupPosition === "middle"
      ? "aqe-button aqe-split-primary aqe-split-primary-middle"
      : "aqe-button aqe-split-primary",
  );

  const currentPrimaryTitle = $derived(primaryTitle(button, outputFormat, denoiseAlgorithm, sizeReductionMode));
  const currentValue = $derived(currentValueLabel(button, groupSlug, {
    denoiseAlgorithm,
    dpdfnetAttnLimitDb,
    graphConnectShortDropoutsMs,
    graphRecordingCondition,
    graphSmoothness,
    graphVoiceLock,
    graphVoiceRange,
    outputFormat,
    sizeReductionMode,
    sizeReductionBitrateKbps,
    sizeReductionSampleRateHz,
    sizeReductionChannels,
    pauseAggressiveness,
    pauseDetectionAlgorithm,
    pitchHumMode,
    shareTarget,
    speedStep,
    voiceRecordingCountdownSeconds,
    volumeStepDb,
  }));

  const {
    syncFromState,
    applyVolumeStep,
    applySpeedStep,
    applyPauseAggressiveness,
    applyPauseDetectionAlgorithm,
    applyPauseThreshold,
    applyPauseMinSilenceSeconds,
    applyPauseMinSpeechSeconds,
    applyPausePreprocessDenoise,
    applyDenoiseAlgorithm,
    applyDpdfnetAttnLimitDb,
    applyOutputFormat,
    applySizeReductionMode,
    applySizeReductionBitrateKbps,
    applySizeReductionSampleRateHz,
    applySizeReductionChannels,
    applyPitchHumMode,
    applyShareTarget,
    applyGraphVoiceRange,
    applyGraphRecordingCondition,
    applyGraphSmoothness,
    applyGraphConnectShortDropouts,
    applyGraphVoiceLock,
    applyVoiceRecordingCountdownSeconds,
  } = createSplitButtonStateHandlers(
    () => target.ord,
    {
    setVolumeStepDb: (value) => {
      volumeStepDb = value;
    },
    setSpeedStep: (value) => {
      speedStep = value;
    },
    setPauseAggressiveness: (value) => {
      pauseAggressiveness = value;
    },
    setPauseDetectionAlgorithm: (value) => {
      pauseDetectionAlgorithm = value;
    },
    setPauseThreshold: (value) => {
      pauseThreshold = value;
    },
    setPauseMinSilenceSeconds: (value) => {
      pauseMinSilenceSeconds = value;
    },
    setPauseMinSpeechSeconds: (value) => {
      pauseMinSpeechSeconds = value;
    },
    setPausePreprocessDenoise: (value) => {
      pausePreprocessDenoise = value;
    },
    setDenoiseAlgorithm: (value) => {
      denoiseAlgorithm = value;
    },
    setDpdfnetAttnLimitDb: (value) => {
      dpdfnetAttnLimitDb = value;
    },
    setOutputFormat: (value) => {
      outputFormat = value;
    },
    setSizeReductionMode: (value) => {
      sizeReductionMode = value;
    },
    setSizeReductionBitrateKbps: (value) => {
      sizeReductionBitrateKbps = value;
    },
    setSizeReductionSampleRateHz: (value) => {
      sizeReductionSampleRateHz = value;
    },
    setSizeReductionChannels: (value) => {
      sizeReductionChannels = value;
    },
    setPitchHumMode: (value) => {
      pitchHumMode = value;
    },
    setShareTarget: (value) => {
      shareTarget = value;
    },
    setGraphVoiceRange: (value) => {
      graphVoiceRange = value;
    },
    setGraphRecordingCondition: (value) => {
      graphRecordingCondition = value;
    },
    setGraphSmoothness: (value) => {
      graphSmoothness = value;
    },
    setGraphConnectShortDropouts: (value) => {
      graphConnectShortDropoutsMs = value;
    },
    setGraphVoiceLock: (value) => {
      graphVoiceLock = value;
    },
    setVoiceRecordingCountdownSeconds: (value) => {
      voiceRecordingCountdownSeconds = value;
    },
  });

  const menuTitle = $derived(
    t("editor.split.menu_title", {
      label: menuTextLabel,
      value: currentValue,
    }),
  );

  function close(): void {
    open = false;
  }

  function dispatchCommand(command: ButtonSpec["command"]): void {
    window.dispatchEvent(new Event(CLOSE_SPLIT_MENUS_EVENT));
    close();
    const payload = command === "aqe:play-recording" ? undefined : buildSplitCommandPayload(command, targetOrd);
    send(command, targetNode, targetOrd, payload);
  }

  function dispatchPrimary(): void {
    if (button.command === "aqe:record-voice") {
      window.dispatchEvent(new Event(CLOSE_SPLIT_MENUS_EVENT));
      close();
      dispatchLearnerRecordingPrimary(targetNode, targetOrd);
      return;
    }
    dispatchCommand(button.command);
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
    const request = buildSplitDefaultSaveRequest(button.command, targetOrd);
    sendSplitDefaultSaveRequest(request);
    syncFromState(promoteSplitDefaultsForField(targetOrd, request.defaults));
    showDefaultSaved();
  }

  function onOpenChange(nextOpen: boolean): void {
    if (nextOpen) syncFromState(getSplitButtonState(targetOrd));
    open = nextOpen;
  }

  onMount(() => {
    syncFromState(getSplitButtonState(targetOrd));
    const handleGraphSplitStateChanged = (event: Event): void => {
      const detail = (event as CustomEvent<GraphSplitStateChangedDetail>).detail;
      if (detail?.ord !== targetOrd) return;
      syncFromState(detail.state ?? getSplitButtonState(targetOrd));
    };
    window.addEventListener(CLOSE_SPLIT_MENUS_EVENT, close);
    window.addEventListener(GRAPH_SPLIT_STATE_CHANGED_EVENT, handleGraphSplitStateChanged);
    return () => {
      window.removeEventListener(CLOSE_SPLIT_MENUS_EVENT, close);
      window.removeEventListener(GRAPH_SPLIT_STATE_CHANGED_EVENT, handleGraphSplitStateChanged);
      if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    };
  });
</script>

{#if showMenu}
  <SplitButtonMenu
    {button}
    {displayMode}
    {groupSlug}
    menuTitle={menuTitle}
    menuSlug={menuSlug}
    menuTextLabel={menuTextLabel}
    {open}
    {onOpenChange}
    onPrimaryClick={dispatchPrimary}
    primaryAriaLabel={currentPrimaryTitle}
    primaryClass={primaryClass}
    primaryDisabled={primaryInitiallyDisabled(button.command)}
    primaryDisabledReason={primaryDisabledReason(button.command)}
    primarySlug={commandSlug}
    primaryTitle={currentPrimaryTitle}
    {showPrimary}
    {showRunButton}
    {sourceFilename}
    targetOrd={targetOrd}
    {denoiseAlgorithm}
    {dpdfnetAttnLimitDb}
    {graphVoiceRange}
    {graphRecordingCondition}
    {graphSmoothness}
    {graphConnectShortDropoutsMs}
    {graphVoiceLock}
    {pauseAggressiveness}
    {pauseDetectionAlgorithm}
    {pauseMinSilenceSeconds}
    {pauseMinSpeechSeconds}
    {pausePreprocessDenoise}
    {pauseThreshold}
    {outputFormat}
    {sizeReductionMode}
    {sizeReductionBitrateKbps}
    {sizeReductionSampleRateHz}
    {sizeReductionChannels}
    {pitchHumMode}
    {shareTarget}
    {speedStep}
    {volumeStepDb}
    {defaultSaved}
    {voiceRecordingCountdownSeconds}
    applyGraphConnectShortDropouts={applyGraphConnectShortDropouts}
    applyGraphRecordingCondition={applyGraphRecordingCondition}
    applyGraphSmoothness={applyGraphSmoothness}
    applyGraphVoiceLock={applyGraphVoiceLock}
    applyGraphVoiceRange={applyGraphVoiceRange}
    applyVoiceRecordingCountdownSeconds={applyVoiceRecordingCountdownSeconds}
    applyDenoiseAlgorithm={applyDenoiseAlgorithm}
    applyDpdfnetAttnLimitDb={applyDpdfnetAttnLimitDb}
    applyOutputFormat={applyOutputFormat}
    applyPauseAggressiveness={applyPauseAggressiveness}
    applyPauseDetectionAlgorithm={applyPauseDetectionAlgorithm}
    applyPauseMinSilenceSeconds={applyPauseMinSilenceSeconds}
    applyPauseMinSpeechSeconds={applyPauseMinSpeechSeconds}
    applyPausePreprocessDenoise={applyPausePreprocessDenoise}
    applyPauseThreshold={applyPauseThreshold}
    applyPitchHumMode={applyPitchHumMode}
    applySaveDefault={saveCurrentDefaults}
    applyShareTarget={applyShareTarget}
    applySizeReductionBitrateKbps={applySizeReductionBitrateKbps}
    applySizeReductionChannels={applySizeReductionChannels}
    applySizeReductionMode={applySizeReductionMode}
    applySizeReductionSampleRateHz={applySizeReductionSampleRateHz}
    applySpeedStep={applySpeedStep}
    applyVolumeStep={applyVolumeStep}
    onRunCommand={dispatchCommand}
  />
{:else if showPrimary}
  <SplitButtonPrimary
    ariaLabel={currentPrimaryTitle}
    activeIcon={button.activeIcon}
    command={button.command}
    disabled={primaryInitiallyDisabled(button.command)}
    disabledReason={primaryDisabledReason(button.command)}
    {displayMode}
    icon={button.icon}
    label={button.label}
    onClick={dispatchPrimary}
    ord={targetOrd}
    primaryClass={primaryClass}
    slug={commandSlug}
    title={currentPrimaryTitle}
  />
{/if}
