<script lang="ts">
  import { Popover } from "bits-ui";
  import { t } from "../lib/i18n.js";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import GraphSplitPopoverContent from "./GraphSplitPopoverContent.svelte";
  import RecordingSplitOptions from "./RecordingSplitOptions.svelte";
  import SplitButtonPrimary from "./SplitButtonPrimary.svelte";
  import SplitValueOptions from "./SplitValueOptions.svelte";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import type { GraphRecordingCondition, GraphSmoothness, GraphVoiceLock, GraphVoiceRange } from "./graph-settings.js";
  import type { ButtonSpec, FieldSplitButtonState } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type OutputFormatValue = FieldSplitButtonState["outputFormat"];
  type PauseDetectionAlgorithm = FieldSplitButtonState["pauseDetectionAlgorithm"];
  type PauseAggressiveness = FieldSplitButtonState["pauseAggressiveness"];
  type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
  type SizeReductionMode = FieldSplitButtonState["sizeReductionMode"];
  type ShareTarget = FieldSplitButtonState["shareTarget"];

  const {
    button,
    displayMode,
    groupSlug,
    menuTitle,
    menuSlug,
    menuTextLabel,
    open,
    onOpenChange,
    onPrimaryClick,
    primaryAriaLabel,
    primaryClass,
    primaryDisabled,
    primaryDisabledReason,
    primarySlug,
    primaryTitle,
    showPrimary,
    showRunButton,
    sourceFilename = null,
    targetOrd,
    denoiseAlgorithm,
    dpdfnetAttnLimitDb,
    graphVoiceRange,
    graphRecordingCondition,
    graphSmoothness,
    graphConnectShortDropoutsMs,
    graphVoiceLock,
    pauseAggressiveness,
    pauseDetectionAlgorithm,
    pauseMinSilenceSeconds,
    pauseMinSpeechSeconds,
    pausePreprocessDenoise,
    pauseThreshold,
    outputFormat,
    sizeReductionMode,
    sizeReductionBitrateKbps,
    sizeReductionSampleRateHz,
    sizeReductionChannels,
    pitchHumMode,
    shareTarget,
    speedStep,
    volumeStepDb,
    defaultSaved,
    voiceRecordingCountdownSeconds,
    applyGraphConnectShortDropouts,
    applyGraphRecordingCondition,
    applyGraphSmoothness,
    applyGraphVoiceLock,
    applyGraphVoiceRange,
    applyVoiceRecordingCountdownSeconds,
    applyDenoiseAlgorithm,
    applyDpdfnetAttnLimitDb,
    applyOutputFormat,
    applyPauseAggressiveness,
    applyPauseDetectionAlgorithm,
    applyPauseMinSilenceSeconds,
    applyPauseMinSpeechSeconds,
    applyPausePreprocessDenoise,
    applyPauseThreshold,
    applyPitchHumMode,
    applySaveDefault,
    applyShareTarget,
    applySizeReductionBitrateKbps,
    applySizeReductionChannels,
    applySizeReductionMode,
    applySizeReductionSampleRateHz,
    applySpeedStep,
    applyVolumeStep,
    onRunCommand,
  }: {
    button: ButtonSpec;
    displayMode: EditorButtonDisplayMode;
    groupSlug: "speed" | "volume" | undefined;
    menuTitle: string;
    menuSlug: string;
    menuTextLabel: string;
    open: boolean;
    onOpenChange: (nextOpen: boolean) => void;
    onPrimaryClick: () => void;
    primaryAriaLabel: string;
    primaryClass: string;
    primaryDisabled: boolean;
    primaryDisabledReason: string | undefined;
    primarySlug: string;
    primaryTitle: string;
    showPrimary: boolean;
    showRunButton: boolean;
    sourceFilename?: string | null;
    targetOrd: number;
    denoiseAlgorithm: DenoiseAlgorithm;
    dpdfnetAttnLimitDb: number;
    graphVoiceRange: GraphVoiceRange;
    graphRecordingCondition: GraphRecordingCondition;
    graphSmoothness: GraphSmoothness;
    graphConnectShortDropoutsMs: number;
    graphVoiceLock: GraphVoiceLock;
    pauseAggressiveness: PauseAggressiveness;
    pauseDetectionAlgorithm: PauseDetectionAlgorithm;
    pauseMinSilenceSeconds: number;
    pauseMinSpeechSeconds: number;
    pausePreprocessDenoise: boolean;
    pauseThreshold: number;
    outputFormat: OutputFormatValue;
    sizeReductionMode: SizeReductionMode;
    sizeReductionBitrateKbps: number;
    sizeReductionSampleRateHz: number;
    sizeReductionChannels: number;
    pitchHumMode: PitchHumMode;
    shareTarget: ShareTarget;
    speedStep: number;
    volumeStepDb: number;
    defaultSaved: boolean;
    voiceRecordingCountdownSeconds: number;
    applyGraphConnectShortDropouts: (value: number) => void;
    applyGraphRecordingCondition: (value: GraphRecordingCondition) => void;
    applyGraphSmoothness: (value: GraphSmoothness) => void;
    applyGraphVoiceLock: (value: GraphVoiceLock) => void;
    applyGraphVoiceRange: (value: GraphVoiceRange) => void;
    applyVoiceRecordingCountdownSeconds: (value: number) => void;
    applyDenoiseAlgorithm: (value: DenoiseAlgorithm) => void;
    applyDpdfnetAttnLimitDb: (value: number) => void;
    applyOutputFormat: (value: OutputFormatValue) => void;
    applyPauseAggressiveness: (value: PauseAggressiveness) => void;
    applyPauseDetectionAlgorithm: (value: PauseDetectionAlgorithm) => void;
    applyPauseMinSilenceSeconds: (value: number) => void;
    applyPauseMinSpeechSeconds: (value: number) => void;
    applyPausePreprocessDenoise: (value: boolean) => void;
    applyPauseThreshold: (value: number) => void;
    applyPitchHumMode: (value: PitchHumMode) => void;
    applySaveDefault: () => void;
    applyShareTarget: (value: ShareTarget) => void;
    applySizeReductionBitrateKbps: (value: number) => void;
    applySizeReductionChannels: (value: number) => void;
    applySizeReductionMode: (value: SizeReductionMode) => void;
    applySizeReductionSampleRateHz: (value: number) => void;
    applySpeedStep: (value: number) => void;
    applyVolumeStep: (value: number) => void;
    onRunCommand: (command: ButtonSpec["command"]) => void;
  } = $props();
</script>

<Popover.Root open={open} onOpenChange={onOpenChange}>
  <span class="aqe-split-button">
    {#if showPrimary}
      <SplitButtonPrimary
        ariaLabel={primaryAriaLabel}
        activeIcon={button.activeIcon}
        command={button.command}
        disabled={primaryDisabled}
        disabledReason={primaryDisabledReason}
        {displayMode}
        icon={button.icon}
        label={button.label}
        onClick={onPrimaryClick}
        ord={targetOrd}
        primaryClass={primaryClass}
        slug={primarySlug}
        title={primaryTitle}
      />
    {/if}
    <Popover.Trigger
      class="aqe-button aqe-icon-only aqe-split-menu-button"
      data-aqe-tooltip-content={menuTitle}
      data-testid={`aqe-split-${targetOrd}-${menuSlug}-menu`}
      aria-label={menuTitle}
    >
      <EditorCommandIcon icon="chevron-down" />
      <span class="aqe-button-label">{t("editor.split.options")}</span>
    </Popover.Trigger>
    <Popover.Content
      align="center"
      arrowPadding={14}
      class={`aqe-ui-root aqe-split-popover${button.command === "aqe:analyze" ? " aqe-graph-split-popover" : ""}`}
      collisionPadding={8}
      data-testid={`aqe-split-${targetOrd}-${menuSlug}-popover`}
      onCloseAutoFocus={(event) => event.preventDefault()}
      side="bottom"
      sideOffset={4}
      strategy="fixed"
      trapFocus={false}
    >
      <Popover.Arrow
        class="aqe-split-popover-arrow"
        data-testid={`aqe-split-${targetOrd}-${menuSlug}-arrow`}
        height={8}
        width={16}
      />
      {#if button.command === "aqe:analyze"}
        <GraphSplitPopoverContent
          connectShortDropoutsMs={graphConnectShortDropoutsMs}
          menuLabel={menuTextLabel}
          menuSlug={menuSlug}
          onConnectShortDropouts={applyGraphConnectShortDropouts}
          onRecordingCondition={applyGraphRecordingCondition}
          onRun={onPrimaryClick}
          onSaveDefault={applySaveDefault}
          onSmoothness={applyGraphSmoothness}
          onVoiceLock={applyGraphVoiceLock}
          onVoiceRange={applyGraphVoiceRange}
          recordingCondition={graphRecordingCondition}
          saved={defaultSaved}
          smoothness={graphSmoothness}
          targetOrd={targetOrd}
          voiceLock={graphVoiceLock}
          voiceRange={graphVoiceRange}
        />
      {:else if button.command === "aqe:record-voice"}
        <RecordingSplitOptions
          countdownSeconds={voiceRecordingCountdownSeconds}
          onCountdownSeconds={applyVoiceRecordingCountdownSeconds}
          onSaveDefault={applySaveDefault}
          saveDefaultSaved={defaultSaved}
          slug={menuSlug}
          targetOrd={targetOrd}
        />
      {:else}
        <SplitValueOptions
          {button}
          {denoiseAlgorithm}
          dpdfnetAttnLimitDb={dpdfnetAttnLimitDb}
          {groupSlug}
          menuLabel={menuTextLabel}
          onChange={() => {}}
          onDenoiseAlgorithm={applyDenoiseAlgorithm}
          onDpdfnetAttnLimitDb={applyDpdfnetAttnLimitDb}
          onOutputFormat={applyOutputFormat}
          onPauseAggressiveness={applyPauseAggressiveness}
          onPauseDetectionAlgorithm={applyPauseDetectionAlgorithm}
          onPauseMinSilenceSeconds={applyPauseMinSilenceSeconds}
          onPauseMinSpeechSeconds={applyPauseMinSpeechSeconds}
          onPausePreprocessDenoise={applyPausePreprocessDenoise}
          onPauseThreshold={applyPauseThreshold}
          onPitchHumMode={applyPitchHumMode}
          onRunCommand={onRunCommand}
          onSaveDefault={applySaveDefault}
          onShareTarget={applyShareTarget}
          onSizeReductionBitrateKbps={applySizeReductionBitrateKbps}
          onSizeReductionChannels={applySizeReductionChannels}
          onSizeReductionMode={applySizeReductionMode}
          onSizeReductionSampleRateHz={applySizeReductionSampleRateHz}
          onSpeedStep={applySpeedStep}
          onVolumeStep={applyVolumeStep}
          pauseAggressiveness={pauseAggressiveness}
          pauseDetectionAlgorithm={pauseDetectionAlgorithm}
          pauseMinSilenceSeconds={pauseMinSilenceSeconds}
          pauseMinSpeechSeconds={pauseMinSpeechSeconds}
          pausePreprocessDenoise={pausePreprocessDenoise}
          pauseThreshold={pauseThreshold}
          outputFormat={outputFormat}
          sizeReductionMode={sizeReductionMode}
          sizeReductionBitrateKbps={sizeReductionBitrateKbps}
          sizeReductionSampleRateHz={sizeReductionSampleRateHz}
          sizeReductionChannels={sizeReductionChannels}
          pitchHumMode={pitchHumMode}
          saveDefaultSaved={defaultSaved}
          shareTarget={shareTarget}
          {showRunButton}
          showSaveDefault={true}
          {sourceFilename}
          speedStep={speedStep}
          targetOrd={targetOrd}
          volumeStepDb={volumeStepDb}
        />
      {/if}
    </Popover.Content>
  </span>
</Popover.Root>
