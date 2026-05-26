<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import {
    graphConnectDropoutsNote,
    graphRecordingConditionNote,
    graphRecordingConditionTooltip,
    graphSmoothnessTooltip,
    graphVoiceLockNote,
    graphVoiceLockTooltip,
    graphVoiceRangeNote,
    graphVoiceRangeTooltip,
  } from "../lib/graph-option-copy.js";
  import { t } from "../lib/i18n.js";
  import {
    formatGraphRecordingCondition,
    formatGraphSmoothness,
    formatGraphVoiceLock,
    formatGraphVoiceRange,
    GRAPH_RECORDING_CONDITIONS,
    GRAPH_SMOOTHNESSES,
    GRAPH_VOICE_LOCKS,
    GRAPH_VOICE_RANGES,
  } from "./graph-split-values.js";
  import type {
    GraphRecordingCondition,
    GraphSmoothness,
    GraphVoiceLock,
    GraphVoiceRange,
  } from "./graph-settings.js";

  const {
    connectShortDropoutsMs,
    onConnectShortDropouts,
    onRecordingCondition,
    onSmoothness,
    onVoiceLock,
    onVoiceRange,
    recordingCondition,
    slug,
    smoothness,
    targetOrd,
    voiceLock,
    voiceRange,
  }: {
    connectShortDropoutsMs: number;
    onConnectShortDropouts: (value: number) => void;
    onRecordingCondition: (value: GraphRecordingCondition) => void;
    onSmoothness: (value: GraphSmoothness) => void;
    onVoiceLock: (value: GraphVoiceLock) => void;
    onVoiceRange: (value: GraphVoiceRange) => void;
    recordingCondition: GraphRecordingCondition;
    slug: string;
    smoothness: GraphSmoothness;
    targetOrd: number;
    voiceLock: GraphVoiceLock;
    voiceRange: GraphVoiceRange;
  } = $props();
</script>

<div class="aqe-graph-options">
  <div class="aqe-graph-option">
    <span>{t("editor.graph.options.voice_range")}</span>
    <span class="aqe-graph-option-note">{graphVoiceRangeNote()}</span>
    <div
      class="aqe-split-presets aqe-graph-option-group"
      role="radiogroup"
      aria-label={t("editor.graph.options.voice_range")}
    >
      {#each GRAPH_VOICE_RANGES as option}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="aqe-button aqe-split-preset aqe-tooltip-target"
              data-testid={`aqe-split-${targetOrd}-${slug}-voice-range-${option}`}
              data-aqe-tooltip-content={graphVoiceRangeTooltip(option)}
              role="radio"
              aria-checked={voiceRange === option ? "true" : "false"}
              tabindex={voiceRange === option ? 0 : -1}
              onclick={() => onVoiceRange(option)}
            >
              {formatGraphVoiceRange(option)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </div>

  <div class="aqe-graph-option">
    <span>{t("editor.graph.options.recording_condition")}</span>
    <span class="aqe-graph-option-note">{graphRecordingConditionNote()}</span>
    <div
      class="aqe-split-presets aqe-graph-option-group"
      role="radiogroup"
      aria-label={t("editor.graph.options.recording_condition")}
    >
      {#each GRAPH_RECORDING_CONDITIONS as option}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="aqe-button aqe-split-preset aqe-tooltip-target"
              data-testid={`aqe-split-${targetOrd}-${slug}-recording-condition-${option}`}
              data-aqe-tooltip-content={graphRecordingConditionTooltip(option)}
              role="radio"
              aria-checked={recordingCondition === option ? "true" : "false"}
              tabindex={recordingCondition === option ? 0 : -1}
              onclick={() => onRecordingCondition(option)}
            >
              {formatGraphRecordingCondition(option)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </div>

  <div class="aqe-graph-option">
    <span>{t("editor.graph.options.voice_lock")}</span>
    <span class="aqe-graph-option-note">{graphVoiceLockNote()}</span>
    <div
      class="aqe-split-presets aqe-graph-option-group"
      role="radiogroup"
      aria-label={t("editor.graph.options.voice_lock")}
    >
      {#each GRAPH_VOICE_LOCKS as option}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="aqe-button aqe-split-preset aqe-tooltip-target"
              data-testid={`aqe-split-${targetOrd}-${slug}-voice-lock-${option}`}
              data-aqe-tooltip-content={graphVoiceLockTooltip(option)}
              role="radio"
              aria-checked={voiceLock === option ? "true" : "false"}
              tabindex={voiceLock === option ? 0 : -1}
              onclick={() => onVoiceLock(option)}
            >
              {formatGraphVoiceLock(option)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </div>

  <div class="aqe-graph-option">
    <span>{t("editor.graph.options.smoothness")}</span>
    <div
      class="aqe-split-presets aqe-graph-option-group"
      role="radiogroup"
      aria-label={t("editor.graph.options.smoothness")}
    >
      {#each GRAPH_SMOOTHNESSES as option}
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="aqe-button aqe-split-preset aqe-tooltip-target"
              data-testid={`aqe-split-${targetOrd}-${slug}-smoothness-${option}`}
              data-aqe-tooltip-content={graphSmoothnessTooltip(option)}
              role="radio"
              aria-checked={smoothness === option ? "true" : "false"}
              tabindex={smoothness === option ? 0 : -1}
              onclick={() => onSmoothness(option)}
            >
              {formatGraphSmoothness(option)}
            </button>
          {/snippet}
        </AqeTooltip>
      {/each}
    </div>
  </div>

  <label class="aqe-graph-option">
    <span>{t("editor.graph.options.connect_dropouts")}</span>
    <span class="aqe-graph-option-note">{graphConnectDropoutsNote()}</span>
    <input
      data-testid={`aqe-split-${targetOrd}-${slug}-connect-dropouts`}
      type="range"
      min="0"
      max="500"
      step="30"
      value={connectShortDropoutsMs}
      oninput={(event) => onConnectShortDropouts((event.currentTarget as HTMLInputElement).valueAsNumber)}
    />
    <span class="aqe-graph-option-value">{connectShortDropoutsMs} ms</span>
  </label>
</div>
