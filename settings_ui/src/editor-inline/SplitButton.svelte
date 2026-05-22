<script lang="ts">
  import { onMount, tick } from "svelte";

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
  import type { GraphRecordingCondition, GraphSmoothness, GraphVoiceLock, GraphVoiceRange } from "./graph-settings.js";
  import type { ButtonSpec, FieldSplitButtonState, FieldTarget } from "./types.js";

  type DenoiseAlgorithm = FieldSplitButtonState["denoiseAlgorithm"];
  type OutputFormatValue = FieldSplitButtonState["outputFormat"];
  type PitchHumMode = FieldSplitButtonState["pitchHumMode"];
  type ShareTarget = FieldSplitButtonState["shareTarget"];

  const POPOVER_GAP_PX = 4;
  const VIEWPORT_MARGIN_PX = 8;
  const HIDDEN_POPOVER_STYLE = "visibility: hidden;";

  const { button, target }: { button: ButtonSpec; target: FieldTarget } = $props();
  let wrapper = $state<HTMLSpanElement>();
  let popover = $state<HTMLDivElement>();
  let open = $state(false);
  let popoverStyle = $state(HIDDEN_POPOVER_STYLE);
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

  function close(): void {
    open = false;
    popoverStyle = HIDDEN_POPOVER_STYLE;
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

  function toggle(event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    open = !open;
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
    void updatePopoverPlacement();
  }

  function clamp(value: number, min: number, max: number): number {
    return Math.min(Math.max(value, min), max);
  }

  function viewportBounds(): { width: number; height: number } {
    return {
      width: window.innerWidth || document.documentElement.clientWidth,
      height: window.innerHeight || document.documentElement.clientHeight,
    };
  }

  function positionPopover(): void {
    if (!wrapper || !popover) return;

    const anchorRect = wrapper.getBoundingClientRect();
    const popoverRect = popover.getBoundingClientRect();
    const viewport = viewportBounds();
    const maxLeft = Math.max(VIEWPORT_MARGIN_PX, viewport.width - popoverRect.width - VIEWPORT_MARGIN_PX);
    const maxTop = Math.max(VIEWPORT_MARGIN_PX, viewport.height - popoverRect.height - VIEWPORT_MARGIN_PX);
    const centeredLeft = anchorRect.left + anchorRect.width / 2 - popoverRect.width / 2;
    const belowTop = anchorRect.bottom + POPOVER_GAP_PX;
    const aboveTop = anchorRect.top - popoverRect.height - POPOVER_GAP_PX;
    const fitsBelow = belowTop + popoverRect.height <= viewport.height - VIEWPORT_MARGIN_PX;
    const fitsAbove = aboveTop >= VIEWPORT_MARGIN_PX;
    const preferredTop = !fitsBelow && fitsAbove ? aboveTop : belowTop;

    popoverStyle = [
      `left: ${clamp(centeredLeft, VIEWPORT_MARGIN_PX, maxLeft)}px;`,
      `top: ${clamp(preferredTop, VIEWPORT_MARGIN_PX, maxTop)}px;`,
      `max-height: ${Math.max(80, viewport.height - VIEWPORT_MARGIN_PX * 2)}px;`,
    ].join(" ");
  }

  async function updatePopoverPlacement(): Promise<void> {
    if (!open) return;
    await tick();
    if (!open) return;
    positionPopover();
  }

  function onViewportChange(): void {
    void updatePopoverPlacement();
  }

  function onDocumentPointerDown(event: MouseEvent): void {
    if (!open || !wrapper) return;
    if (event.target instanceof Node && wrapper.contains(event.target)) return;
    close();
  }

  function onDocumentKeyDown(event: KeyboardEvent): void {
    if (event.key === "Escape") close();
  }

  $effect(() => {
    if (open) {
      void updatePopoverPlacement();
    } else {
      popoverStyle = HIDDEN_POPOVER_STYLE;
    }
  });

  onMount(() => {
    syncFromState(getSplitButtonState(target.ord));
    document.addEventListener("mousedown", onDocumentPointerDown, true);
    document.addEventListener("keydown", onDocumentKeyDown, true);
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("scroll", onViewportChange, true);
    return () => {
      document.removeEventListener("mousedown", onDocumentPointerDown, true);
      document.removeEventListener("keydown", onDocumentKeyDown, true);
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("scroll", onViewportChange, true);
      if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    };
  });
</script>

<span class="aqe-split-button" bind:this={wrapper}>
  <button
    type="button"
    class:aqe-icon-only={button.iconOnly === true}
    class="aqe-button aqe-split-primary"
    data-aqe-command={button.command}
    data-aqe-button-state={initialButtonState()}
    data-testid={`aqe-button-${target.ord}-${slug()}`}
    title={primaryTitle()}
    aria-label={primaryTitle()}
    onmousedown={(event) => event.preventDefault()}
    onclick={dispatchPrimary}
  >
    <EditorCommandIcon icon={button.icon} />
    <span class="aqe-button-label">{button.label}</span>
  </button>
  <button
    type="button"
    class="aqe-button aqe-icon-only aqe-split-menu-button"
    data-testid={`aqe-split-${target.ord}-${slug()}-menu`}
    title={t("editor.split.options")}
    aria-label={t("editor.split.options")}
    aria-expanded={open ? "true" : "false"}
    onmousedown={(event) => event.preventDefault()}
    onclick={toggle}
  >
    <EditorCommandIcon icon="chevron-down" />
    <span class="aqe-button-label">{t("editor.split.options")}</span>
  </button>
  {#if open}
    <div
      bind:this={popover}
      class="aqe-split-popover"
      class:aqe-graph-split-popover={button.command === "aqe:analyze"}
      data-testid={`aqe-split-${target.ord}-${slug()}-popover`}
      style={popoverStyle}
    >
      {#if button.command === "aqe:analyze"}
        <div class="aqe-split-popover-header aqe-split-popover-header-with-action">
          <span class="aqe-split-popover-title">
            <strong>{button.label}</strong>
            <span>{graphSummary}</span>
          </span>
          <SplitDefaultSaveButton
            onSave={saveCurrentDefaults}
            saved={defaultSaved}
            testId={`aqe-split-${target.ord}-${slug()}-save-default`}
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
          slug={slug()}
          smoothness={graphSmoothness}
          targetOrd={target.ord}
          voiceLock={graphVoiceLock}
          voiceRange={graphVoiceRange}
        />
      {:else}
        <SplitValueOptions
          {button}
          denoiseAlgorithm={denoiseAlgorithm}
          onChange={() => void updatePopoverPlacement()}
          onDenoiseAlgorithm={applyDenoiseAlgorithm}
          onDpdfnetAttnLimitDb={applyDpdfnetAttnLimitDb}
          onOutputFormat={applyOutputFormat}
          onPauseAggressiveness={applyPauseAggressiveness}
          onPitchHumMode={applyPitchHumMode}
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
    </div>
  {/if}
</span>
